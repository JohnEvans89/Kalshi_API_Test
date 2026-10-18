#!/usr/bin/env python3
"""
Pyth Indices live dashboard (PYTHOIL, SILVER, GOLD, GAS, PALLADIUM)
- Auto-refreshes free fallback token from app.pyth.com
- Polls Pyth Pro latest_price for multiple feeds
- Serves a live dashboard at http://127.0.0.1:8050

Manual previous price
---------------------
Delta on each card is current price minus "prev".
Set prev in MANUAL_PREV below, or override it live from the dashboard
(POST /api/prev). A set value sticks until you clear it.
None means "use the previous poll sample".
"""

from __future__ import annotations

import base64
import json
import ssl
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Deque, Dict, List, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

TOKEN_URL = "https://app.pyth.com/api/lazer/token"
PRICE_URL = "https://pyth-lazer.dourolabs.app/v1/latest_price"

# Feed registry: key used in UI / API -> metadata
FEEDS: Dict[str, Dict[str, Any]] = {
    "PYTHOIL": {
        "feed_id": 3063,
        "symbol": "Commodities.Index.PYTHOIL/USD",
        "label": "PYTHOIL / USD",
        "color": "#3b82f6",
        "decimals": 5,
    },
    "SILVER": {
        "feed_id": 3154,
        "symbol": "Metal.Index.SILVER/USD",
        "label": "SILVER / USD",
        "color": "#c0c7d2",
        "decimals": 5,
    },
    "GOLD": {
        "feed_id": 3712,
        "symbol": "Metal.Index.1OZGOLD/USD",
        "label": "GOLD / USD",
        "color": "#ffcd05",
        "decimals": 5,
    },
    "GAS": {
        "feed_id": 3265,
        "symbol": "Commodities.Index.NATGAS/USD",
        "label": "NATGAS / USD",
        "color": "#f5c542",
        "decimals": 5,
    },
    "PALLADIUM": {
        "feed_id": 1780,
        "symbol": "Metal.XPD/USD",
        "label": "PALLADIUM / US DOLLAR",
        "color": "#f5c542",
        "decimals": 5,
    },
}

# Manual previous price used for the dashboard delta.
# float  -> pin that baseline (current - prev)
# None   -> fall back to the previous poll sample
MANUAL_PREV: Dict[str, Optional[float]] = {
    "PYTHOIL": 93.45,
    "SILVER": 60.685,
    "GOLD": 4176.61,
    "GAS": 2.97733,
    "PALLADIUM": None,
}

FEED_IDS: List[int] = [v["feed_id"] for v in FEEDS.values()]
ID_TO_KEY = {v["feed_id"]: k for k, v in FEEDS.items()}

POLL_INTERVAL_SEC = 1
REFRESH_SKEW_SEC = 60
HISTORY_LEN = 300
HOST = "0.0.0.0"
PORT = 8050


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        import certifi

        ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    return ctx


SSL_CONTEXT = make_ssl_context()


def http_json(
    method: str,
    url: str,
    body: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> Any:
    data = None
    req_headers = {
        "Accept": "application/json",
        "User-Agent": "pyth-indices-dashboard/1.1",
    }
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=req_headers, method=method)
    with urlopen(req, timeout=15, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode("utf-8"))


class PriceStore:
    def __init__(self, manual_prev: Dict[str, Optional[float]]) -> None:
        self.lock = threading.Lock()
        # key -> latest sample
        self.latest: Dict[str, Dict[str, Any]] = {}
        # key -> deque of samples
        self.history: Dict[str, Deque[Dict[str, Any]]] = {
            k: deque(maxlen=HISTORY_LEN) for k in FEEDS
        }
        # key -> pinned previous price, or None to use the prior sample
        self.prev: Dict[str, Optional[float]] = {
            k: manual_prev.get(k) for k in FEEDS
        }
        self.last_error: Optional[str] = None

    def update_many(self, samples: List[Dict[str, Any]]) -> None:
        with self.lock:
            for sample in samples:
                key = sample["key"]
                self.latest[key] = sample
                self.history[key].append(sample)
            self.last_error = None

    def set_error(self, msg: str) -> None:
        with self.lock:
            self.last_error = msg

    def set_prev(self, key: str, price: Optional[float]) -> None:
        if key not in FEEDS:
            raise KeyError(key)
        if price is not None and not isinstance(price, (int, float)):
            raise TypeError("price must be a number or null")
        with self.lock:
            self.prev[key] = None if price is None else float(price)

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "feeds": {
                    k: {
                        "meta": {
                            "feed_id": FEEDS[k]["feed_id"],
                            "symbol": FEEDS[k]["symbol"],
                            "label": FEEDS[k]["label"],
                            "color": FEEDS[k]["color"],
                            "decimals": FEEDS[k]["decimals"],
                        },
                        "latest": self.latest.get(k),
                        "history": list(self.history[k]),
                        "prev": self.prev.get(k),
                        "prev_source": "manual" if self.prev.get(k) is not None else "sample",
                    }
                    for k in FEEDS
                },
                "last_error": self.last_error,
                "server_time_utc": utc_now().isoformat(),
            }


class PythClient:
    def __init__(self) -> None:
        self.token: Optional[str] = None
        self.expires_at = 0.0

    def _decode_exp(self, token: str) -> float:
        try:
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            return float(claims["exp"])
        except Exception:
            return time.time() + 14 * 60

    def refresh_token(self) -> None:
        data = http_json("POST", TOKEN_URL, body={})
        tok = data["fallbackToken"]["accessToken"]
        self.token = tok
        self.expires_at = self._decode_exp(tok)
        exp_iso = datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat()
        print(f"[{utc_now().isoformat()}] token refreshed, expires {exp_iso}")

    def ensure_token(self) -> None:
        if not self.token or time.time() >= (self.expires_at - REFRESH_SKEW_SEC):
            self.refresh_token()

    def fetch_prices(self) -> List[Dict[str, Any]]:
        self.ensure_token()
        body = {
            "priceFeedIds": FEED_IDS,
            "properties": ["price", "exponent", "feedUpdateTimestamp"],
            "formats": [],
            "channel": "fixed_rate@1000ms",
            "deliveryFormat": "json",
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            data = http_json("POST", PRICE_URL, body=body, headers=headers)
        except HTTPError as e:
            if e.code in (401, 403, 419):
                self.refresh_token()
                headers = {"Authorization": f"Bearer {self.token}"}
                data = http_json("POST", PRICE_URL, body=body, headers=headers)
            else:
                raise

        polled_at = utc_now().isoformat()
        samples: List[Dict[str, Any]] = []
        for feed in data["parsed"]["priceFeeds"]:
            feed_id = int(feed["priceFeedId"])
            key = ID_TO_KEY.get(feed_id)
            if not key:
                continue
            meta = FEEDS[key]
            expo = int(feed["exponent"])
            raw = int(feed["price"])
            price = raw * (10**expo)
            ts_us = int(
                feed.get("feedUpdateTimestamp")
                or data["parsed"].get("timestampUs")
                or 0
            )
            feed_ts = (
                datetime.fromtimestamp(ts_us / 1_000_000, tz=timezone.utc).isoformat()
                if ts_us
                else None
            )
            samples.append(
                {
                    "key": key,
                    "symbol": meta["symbol"],
                    "feed_id": feed_id,
                    "price": price,
                    "raw_price": raw,
                    "exponent": expo,
                    "feed_update_time_utc": feed_ts,
                    "polled_at_utc": polled_at,
                }
            )
        return samples


store = PriceStore(MANUAL_PREV)
client = PythClient()


def poll_loop() -> None:
    while True:
        try:
            samples = client.fetch_prices()
            store.update_many(samples)
            parts = [f"{s['key']} {s['price']}" for s in samples]
            print(f"[{utc_now().isoformat()}] " + " | ".join(parts))
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            store.set_error(msg)
            print(f"[{utc_now().isoformat()}] error: {msg}")
        time.sleep(POLL_INTERVAL_SEC)


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pyth Indices Dashboard</title>
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #0b1220;
      color: #e8eefc;
    }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0 0 4px; font-size: 1.5rem; }
    .subtitle { color: #9db0d0; margin-bottom: 20px; font-size: .92rem; }
    .widgets {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .card {
      background: #121a2b;
      border: 1px solid #24304a;
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 8px 30px rgba(0,0,0,.25);
    }
    .card h2 {
      margin: 0 0 4px;
      font-size: 1rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dot {
      width: 10px; height: 10px; border-radius: 50%;
      display: inline-block;
    }
    .muted { color: #9db0d0; font-size: .82rem; }
    .price {
      font-size: 2.2rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      margin: 10px 0 4px;
    }
    .up { color: #3dde8c; }
    .down { color: #ff6b7a; }
    .flat { color: #e8eefc; }
    .meta-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 12px;
    }
    .metric {
      background: #0e1626;
      border: 1px solid #24304a;
      border-radius: 10px;
      padding: 10px;
    }
    .label { color: #9db0d0; font-size: .72rem; margin-bottom: 3px; }
    .value { font-weight: 600; font-size: .85rem; word-break: break-all; }
    .prev-row {
      display: flex;
      gap: 6px;
      margin-top: 12px;
      align-items: center;
    }
    .prev-row input {
      flex: 1;
      min-width: 0;
      background: #0e1626;
      color: #e8eefc;
      border: 1px solid #24304a;
      border-radius: 8px;
      padding: 8px 10px;
      font: inherit;
      font-size: .85rem;
    }
    .prev-row button {
      background: #1c2942;
      color: #e8eefc;
      border: 1px solid #24304a;
      border-radius: 8px;
      padding: 8px 10px;
      font: inherit;
      font-size: .78rem;
      cursor: pointer;
    }
    .prev-row button:hover { border-color: #4b628c; }
    canvas {
      width: 100%;
      height: 120px;
      background: #0e1626;
      border-radius: 10px;
      border: 1px solid #24304a;
      margin-top: 12px;
    }
    .status-card { margin-top: 0; }
    .err { color: #ff6b7a; white-space: pre-wrap; margin-top: 6px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Pyth Indices Dashboard</h1>
    <div class="subtitle">Live PYTHOIL · SILVER · GOLD · GAS · PALLADIUM · set a manual prev to pin the delta</div>

    <div class="widgets" id="widgets"></div>

    <div class="card status-card">
      <div class="muted">Status</div>
      <div id="status" class="muted">connecting…</div>
      <div id="server" class="muted"></div>
      <div id="error" class="err"></div>
    </div>
  </div>

<script>
const ORDER = ['PYTHOIL', 'SILVER', 'GOLD', 'GAS', 'PALLADIUM'];
const widgetsEl = document.getElementById('widgets');
const statusEl = document.getElementById('status');
const serverEl = document.getElementById('server');
const errorEl = document.getElementById('error');
const editing = {};

function fmtPrice(p, decimals) {
  if (p == null || Number.isNaN(p)) return '—';
  return Number(p).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function drawChart(canvas, history, color) {
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (!history || !history.length) return;
  const values = history.map(x => x.price);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = (max - min) * 0.08 || 0.01;
  const lo = min - pad, hi = max + pad;
  ctx.strokeStyle = color || '#3b82f6';
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((pt, i) => {
    const x = history.length === 1 ? w / 2 : (i / (history.length - 1)) * (w - 16) + 8;
    const y = h - 8 - ((pt.price - lo) / (hi - lo)) * (h - 16);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function ensureWidgets(feeds) {
  if (widgetsEl.children.length) return;
  for (const key of ORDER) {
    const f = feeds[key];
    if (!f) continue;
    const card = document.createElement('div');
    card.className = 'card';
    card.id = 'card-' + key;
    card.innerHTML = `
      <h2><span class="dot" style="background:${f.meta.color}"></span>${f.meta.label}</h2>
      <div class="muted">${f.meta.symbol} · feed ${f.meta.feed_id}</div>
      <div class="price flat" id="price-${key}">—</div>
      <div class="muted" id="delta-${key}">waiting…</div>
      <div class="meta-row">
        <div class="metric">
          <div class="label">Polled (UTC)</div>
          <div class="value" id="polled-${key}">—</div>
        </div>
        <div class="metric">
          <div class="label">Feed update (UTC)</div>
          <div class="value" id="feedts-${key}">—</div>
        </div>
      </div>
      <div class="prev-row">
        <input id="prev-${key}" type="number" step="any" placeholder="manual prev" />
        <button type="button" data-set="${key}">Set</button>
        <button type="button" data-use="${key}">Use now</button>
        <button type="button" data-clear="${key}">Clear</button>
      </div>
      <canvas id="chart-${key}" width="400" height="120"></canvas>
    `;
    widgetsEl.appendChild(card);
    const input = card.querySelector('#prev-' + key);
    input.addEventListener('focus', () => { editing[key] = true; });
    input.addEventListener('blur', () => { editing[key] = false; });
  }
}

function samplePrev(hist) {
  if (!hist || hist.length < 2) return null;
  return hist[hist.length - 2].price;
}

function updateFeed(key, feed) {
  const decimals = feed.meta.decimals ?? 5;
  const priceEl = document.getElementById('price-' + key);
  const deltaEl = document.getElementById('delta-' + key);
  const polledEl = document.getElementById('polled-' + key);
  const feedtsEl = document.getElementById('feedts-' + key);
  const prevInput = document.getElementById('prev-' + key);
  const canvas = document.getElementById('chart-' + key);
  if (!priceEl) return;

  const hist = feed.history || [];
  drawChart(canvas, hist, feed.meta.color);

  if (prevInput && !editing[key] && document.activeElement !== prevInput) {
    prevInput.value = feed.prev == null ? '' : String(feed.prev);
  }

  if (!feed.latest) {
    priceEl.textContent = '—';
    deltaEl.textContent = 'waiting for first sample…';
    return;
  }

  const p = feed.latest.price;
  priceEl.textContent = fmtPrice(p, decimals);
  polledEl.textContent = feed.latest.polled_at_utc || '—';
  feedtsEl.textContent = feed.latest.feed_update_time_utc || '—';

  const manual = feed.prev;
  const fallback = samplePrev(hist);
  const prev = manual != null ? manual : fallback;
  if (prev == null) {
    priceEl.className = 'price flat';
    deltaEl.textContent = 'first sample · set a manual prev to pin the delta';
    return;
  }
  const diff = p - prev;
  const pct = prev ? (diff / prev) * 100 : 0;
  const cls = diff > 0 ? 'up' : (diff < 0 ? 'down' : 'flat');
  priceEl.className = 'price ' + cls;
  const sign = diff >= 0 ? '+' : '';
  const source = manual != null ? 'manual prev' : 'previous sample';
  deltaEl.textContent =
    `${sign}${diff.toFixed(decimals)} (${sign}${pct.toFixed(3)}%) vs ${source} ${fmtPrice(prev, decimals)}`;
}

async function setPrev(key, price) {
  const res = await fetch('/api/prev', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, price }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || ('HTTP ' + res.status));
  }
  editing[key] = false;
  await refresh();
}

widgetsEl.addEventListener('click', async (ev) => {
  const setKey = ev.target.getAttribute('data-set');
  const useKey = ev.target.getAttribute('data-use');
  const clearKey = ev.target.getAttribute('data-clear');
  try {
    if (setKey) {
      const raw = document.getElementById('prev-' + setKey).value.trim();
      if (!raw) return;
      await setPrev(setKey, Number(raw));
    } else if (useKey) {
      const priceEl = document.getElementById('price-' + useKey);
      const raw = (priceEl.textContent || '').replace(/,/g, '');
      const price = Number(raw);
      if (!Number.isFinite(price)) return;
      document.getElementById('prev-' + useKey).value = String(price);
      await setPrev(useKey, price);
    } else if (clearKey) {
      document.getElementById('prev-' + clearKey).value = '';
      await setPrev(clearKey, null);
    }
  } catch (e) {
    errorEl.textContent = String(e);
  }
});

async function refresh() {
  try {
    const res = await fetch('/api/data', { cache: 'no-store' });
    const data = await res.json();
    serverEl.textContent = 'Server time (UTC): ' + (data.server_time_utc || '—');
    errorEl.textContent = data.last_error || '';
    const feeds = data.feeds || {};
    ensureWidgets(feeds);
    for (const key of ORDER) {
      if (feeds[key]) updateFeed(key, feeds[key]);
    }
    const ready = ORDER.every(k => feeds[k] && feeds[k].latest);
    statusEl.textContent = ready
      ? 'live · polling every few seconds'
      : 'waiting for first successful poll…';
  } catch (e) {
    statusEl.textContent = 'dashboard fetch failed';
    errorEl.textContent = String(e);
  }
}
refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(200, DASHBOARD_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path.startswith("/api/data"):
            body = json.dumps(store.snapshot()).encode("utf-8")
            self._send(200, body, "application/json")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/prev":
            self._send(404, b"not found", "text/plain")
            return
        try:
            payload = self._read_json()
            key = str(payload.get("key", "")).strip()
            if key not in FEEDS:
                self._send(400, b"unknown feed key", "text/plain")
                return
            price = payload.get("price", None)
            if price is not None:
                price = float(price)
            store.set_prev(key, price)
            shown = "cleared" if price is None else price
            print(f"[{utc_now().isoformat()}] manual prev {key} = {shown}")
            body = json.dumps({"ok": True, "key": key, "prev": price}).encode("utf-8")
            self._send(200, body, "application/json")
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send(400, str(exc).encode("utf-8"), "text/plain")


def main() -> None:
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Dashboard: http://127.0.0.1:{PORT}")
    print(
        "Feeds: "
        + ", ".join(f"{k} ({v['feed_id']})" for k, v in FEEDS.items())
    )
    pinned = {k: v for k, v in MANUAL_PREV.items() if v is not None}
    print(f"Manual prev: {pinned or 'none (using previous sample)'}")
    print("Polling with auto token refresh…")
    server.serve_forever()


if __name__ == "__main__":
    main()
