import pandas as pd
import requests
import json
import os
import time

def fetch_pagination_kalshi_current_data(series_name):
    """
    Fetches all current market data for a series using pagination
    and saves it to a CSV file.
    """
    file_path = f"{series_name}_new_curr.csv"
    # Use markets endpoint for current/recent or historical for deeper history
    next_url = f"https://external-api.kalshi.com/trade-api/v2/markets?limit=1000&series_ticker={series_name}"
    page_count = 0

    print(f"Starting data collection for: {series_name}...")

    while next_url:
        response = requests.get(next_url)
        if response.status_code != 200:
            print(f"Error fetching data for {series_name}: {response.status_code}")
            break

        data = response.json()
        markets = data.get("markets", [])

        if not markets:
            print(f"No more markets found for {series_name}.")
            break

        # Process current page
        df_page = pd.DataFrame(markets)

        # Check that event_ticker contains the series_name
        if "event_ticker" in df_page.columns:
            df_page = df_page[df_page["event_ticker"].str.contains(series_name, na=False)]

        if df_page.empty:
            print(f"Page {page_count + 1}: No matching {series_name} rows, skipping.")
        else:
            # Filter columns
            desired_keys = ["event_ticker", "yes_sub_title", "open_time", "close_time", "expiration_value", "floor_strike", "result"]
            existing_keys = [k for k in desired_keys if k in df_page.columns]
            df_page = df_page[existing_keys]

            # Convert timezones to EST
            datetime_columns = ["close_time", "open_time"]
            for col in datetime_columns:
                if col in df_page.columns:
                    df_page[col] = pd.to_datetime(df_page[col], utc=True, errors="coerce")
                    df_page[col] = df_page[col].dt.tz_convert("America/New_York")

            # Save/Append
            if os.path.isfile(file_path) and page_count > 0:
                df_page.to_csv(file_path, mode="a", index=False, header=False)
            else:
                df_page.to_csv(file_path, index=False)

            page_count += 1
            print(f"Page {page_count}: Processed {len(df_page)} rows for {series_name}.")

        # Check for next cursor
        cursor = data.get("cursor")
        if cursor:
            next_url = f"https://external-api.kalshi.com/trade-api/v2/markets?limit=1000&cursor={cursor}&series_ticker={series_name}"
            time.sleep(0.1)
        else:
            next_url = None

    print(f"Finished {series_name}. Total pages processed: {page_count}\n")
def fetch_pagination_kalshi_historical_data(series_name):
    """
    Fetches all historical market data for a series using pagination
    and saves it to a CSV file.
    """
    file_path = f"{series_name}_new_hist.csv"
    # Use markets endpoint for current/recent or historical for deeper history
    next_url = f"https://external-api.kalshi.com/trade-api/v2/historical/markets?limit=1000&series_ticker={series_name}"
    page_count = 0

    print(f"Starting data collection for: {series_name}...")

    while next_url:
        response = requests.get(next_url)
        if response.status_code != 200:
            print(f"Error fetching data for {series_name}: {response.status_code}")
            break

        data = response.json()
        markets = data.get("markets", [])

        if not markets:
            print(f"No more markets found for {series_name}.")
            break

        # Process current page
        df_page = pd.DataFrame(markets)

        # Check that event_ticker contains the series_name
        if "event_ticker" in df_page.columns:
            df_page = df_page[df_page["event_ticker"].str.contains(series_name, na=False)]

        if df_page.empty:
            print(f"Page {page_count + 1}: No matching {series_name} rows, skipping.")
        else:
            # Filter columns
            desired_keys = ["event_ticker", "yes_sub_title", "open_time", "close_time", "expiration_value", "floor_strike", "result"]
            existing_keys = [k for k in desired_keys if k in df_page.columns]
            df_page = df_page[existing_keys]

            # Convert timezones to EST
            datetime_columns = ["close_time", "open_time"]
            for col in datetime_columns:
                if col in df_page.columns:
                    df_page[col] = pd.to_datetime(df_page[col], utc=True, errors="coerce")
                    df_page[col] = df_page[col].dt.tz_convert("America/New_York")

            # Save/Append
            if os.path.isfile(file_path) and page_count > 0:
                df_page.to_csv(file_path, mode="a", index=False, header=False)
            else:
                df_page.to_csv(file_path, index=False)

            page_count += 1
            print(f"Page {page_count}: Processed {len(df_page)} rows for {series_name}.")

        # Check for next cursor
        cursor = data.get("cursor")
        if cursor:
            next_url = f"https://external-api.kalshi.com/trade-api/v2/historical/markets?limit=1000&cursor={cursor}&series_ticker={series_name}"
            time.sleep(0.1)
        else:
            next_url = None

    print(f"Finished {series_name}. Total pages processed: {page_count}\n")

# BNB
fetch_pagination_kalshi_historical_data("KXBNB15M")
fetch_pagination_kalshi_current_data("KXBNB15M")
# BTC
fetch_pagination_kalshi_historical_data("KXBTC15M")
fetch_pagination_kalshi_current_data("KXBTC15M")
# DOGE
fetch_pagination_kalshi_historical_data("KXDOGE15M")
fetch_pagination_kalshi_current_data("KXDOGE15M")
# ETH
fetch_pagination_kalshi_historical_data("KXETH15M")
fetch_pagination_kalshi_current_data("KXETH15M")
# GOLD
fetch_pagination_kalshi_historical_data("KXGOLD15M")
fetch_pagination_kalshi_current_data("KXGOLD15M")
# HYPE  
fetch_pagination_kalshi_historical_data("KXHYPE15M")
fetch_pagination_kalshi_current_data("KXHYPE15M")
# SILVER
fetch_pagination_kalshi_historical_data("KXSILVER15M")
fetch_pagination_kalshi_current_data("KXSILVER15M")
# SOL
fetch_pagination_kalshi_historical_data("KXSOL15M")
fetch_pagination_kalshi_current_data("KXSOL15M")
# XRP
fetch_pagination_kalshi_historical_data("KXXRP15M")
fetch_pagination_kalshi_current_data("KXXRP15M")




# fetch_and_save_kalshi_paging("KXBTC15M")