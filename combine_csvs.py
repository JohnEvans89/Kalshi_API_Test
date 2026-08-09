# #!/usr/bin/env python3
# import argparse
# import csv
# import os
# import sys
# from pathlib import Path
# from typing import List, Dict, Tuple


# def discover_csv_files(paths: List[str]) -> List[Path]:
#     discovered: List[Path] = []
#     seen = set()
#     for raw_path in paths:
#         path = Path(raw_path).expanduser().resolve()
#         if not path.exists():
#             print(f"Skipping missing path: {path}", file=sys.stderr)
#             continue
#         if path.is_file() and path.suffix.lower() == ".csv":
#             if path not in seen:
#                 seen.add(path)
#                 discovered.append(path)
#         elif path.is_dir():
#             for candidate in sorted(path.rglob("*.csv")):
#                 if candidate not in seen:
#                     seen.add(candidate)
#                     discovered.append(candidate)
#     return discovered


# def normalize_row(row: Dict[str, str], fieldnames: List[str]) -> Dict[str, str]:
#     normalized = {field: row.get(field, "") for field in fieldnames}
#     return normalized


# def parse_sort_value(row: Dict[str, str]) -> str:
#     for key in ("timestamp", "date", "time", "datetime"):
#         if row.get(key):
#             return row[key]
#     for value in row.values():
#         if value:
#             return value
#     return ""


# def combine_csvs(input_paths: List[str], output_path: str) -> Tuple[int, int]:
#     csv_files = discover_csv_files(input_paths)
#     if not csv_files:
#         raise FileNotFoundError("No CSV files found")

#     output = Path(output_path).expanduser().resolve()
#     if output.exists() and output in csv_files:
#         csv_files.remove(output)

#     fieldnames: List[str] = []
#     rows: List[Dict[str, str]] = []
#     seen_rows = set()

#     for csv_file in csv_files:
#         with csv_file.open("r", newline="", encoding="utf-8-sig") as handle:
#             reader = csv.DictReader(handle)
#             if not reader.fieldnames:
#                 continue
#             for field in reader.fieldnames:
#                 if field not in fieldnames:
#                     fieldnames.append(field)
#             for raw_row in reader:
#                 normalized = normalize_row(raw_row, fieldnames)
#                 row_key = tuple((key, normalized.get(key, "")) for key in fieldnames)
#                 if row_key in seen_rows:
#                     continue
#                 seen_rows.add(row_key)
#                 rows.append(normalized)

#     rows.sort(key=parse_sort_value)

#     output.parent.mkdir(parents=True, exist_ok=True)
#     with output.open("w", newline="", encoding="utf-8") as handle:
#         writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
#         writer.writeheader()
#         writer.writerows(rows)

#     return len(rows), len(csv_files)


# def main() -> None:
#     parser = argparse.ArgumentParser(description="Combine CSV files, remove duplicates, and sort rows")
#     parser.add_argument("inputs", nargs="+", help="CSV files or directories to process")
#     parser.add_argument("-o", "--output", default="combined_sorted.csv", help="Output CSV file")
#     args = parser.parse_args()

#     try:
#         row_count, file_count = combine_csvs(args.inputs, args.output)
#     except FileNotFoundError as exc:
#         print(str(exc), file=sys.stderr)
#         sys.exit(1)

#     print(f"Processed {file_count} CSV files")
#     print(f"Wrote {row_count} unique rows to {args.output}")


# if __name__ == "__main__":
#     main()



cd /Users/johnnyevans/Documents/GitHub/Kalshi_API_Test/sq && python3 - <<'PY'
import csv, glob, os
from pathlib import Path
files = ['BT3C(1).csv','combined_sorted.csv','BT3eC.csv','BT3eC(1).csv','BTC.csv']
out = Path('combined_sorted.csv')
rows = []
seen = set()
for name in files:
    with open(name, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = tuple(sorted(row.items()))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
rows.sort(key=lambda r: r.get('timestamp') or r.get('date') or r.get('time') or '')
with out.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ['timestamp','price'])
    writer.writeheader()
    writer.writerows(rows)
print(f'wrote {len(rows)} rows to {out}')
PY

'BT3C(1).csv','combined_sorted.csv','BT3eC.csv','BT3eC(1).csv','BTC.csv'