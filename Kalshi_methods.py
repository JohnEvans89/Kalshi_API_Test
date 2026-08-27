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


# cat *DOGE15M_sorted.csv > DOGE_new_merged.csv  
# rm *DOGE15M_sorted.csv 

# cat *ETH15M_sorted.csv > ETH_new_merged.csv
# rm *ETH15M_sorted.csv

# # cat *GOLD15M_sorted.csv > GOLD_new_merged.csv
# # rm *GOLD15M_sorted.csv

# cat *HYPE15M_sorted.csv > HYPE_new_merged.csv
# rm *HYPE15M_sorted.csv  

# # cat *SILVER15M_sorted.csv > SILVER_new_merged.csv
# # rm *SILVER15M_sorted.csv

# cat *SOL15M_sorted.csv > SOL_new_merged.csv
# rm *SOL15M_sorted.csv   

# cat *XRP15M_sorted.csv > XRP_new_merged.csv
# rm *XRP15M_sorted.csv  
def merge(series_name):
    """
    Merges the historical and current CSV files for a given series into a single CSV file.
    """
    hist_file = f"{series_name}_new_hist.csv"
    curr_file = f"{series_name}_new_curr.csv"
    merged_file = f"{series_name}_merged.csv"

    if not os.path.isfile(hist_file):
        print(f"Historical file {hist_file} does not exist. Skipping merge.")
        return
    if not os.path.isfile(curr_file):
        print(f"Current file {curr_file} does not exist. Skipping merge.")
        return

    df_hist = pd.read_csv(hist_file)
    df_curr = pd.read_csv(curr_file)

    # Concatenate and drop duplicates
    df_merged = pd.concat([df_hist, df_curr]).reset_index(drop=True)

    # Save merged file
    df_merged.to_csv(merged_file, index=False)
    print(f"Merged data saved to {merged_file}. Total rows: {len(df_merged)}\n")

def sort_by_event_ticker(series_name):
    """
    Sorts the merged CSV file by event_ticker and saves it.
    """
    merged_file = f"{series_name}_merged.csv"
    sorted_file = f"{series_name}_sorted.csv"

    if not os.path.isfile(merged_file):
        print(f"Merged file {merged_file} does not exist. Skipping sort.")
        return

    df_merged = pd.read_csv(merged_file)

    # Sort by event_ticker
    df_sorted = df_merged.sort_values(by="event_ticker").reset_index(drop=True)

    # Save sorted file
    df_sorted.to_csv(sorted_file, index=False)
    print(f"Sorted data saved to {sorted_file}. Total rows: {len(df_sorted)}\n")


# BNB
fetch_pagination_kalshi_historical_data("KXBNB15M")
fetch_pagination_kalshi_current_data("KXBNB15M")
# # BTC
fetch_pagination_kalshi_historical_data("KXBTC15M")
fetch_pagination_kalshi_current_data("KXBTC15M")
# # DOGE
fetch_pagination_kalshi_historical_data("KXDOGE15M")
fetch_pagination_kalshi_current_data("KXDOGE15M")
# # ETH
fetch_pagination_kalshi_historical_data("KXETH15M")
fetch_pagination_kalshi_current_data("KXETH15M")
# # GOLD
fetch_pagination_kalshi_historical_data("KXGOLD15M")
fetch_pagination_kalshi_current_data("KXGOLD15M")
# # HYPE  
fetch_pagination_kalshi_historical_data("KXHYPE15M")
fetch_pagination_kalshi_current_data("KXHYPE15M")
# # SILVER
fetch_pagination_kalshi_historical_data("KXSILVER15M")
fetch_pagination_kalshi_current_data("KXSILVER15M")
# # SOL
fetch_pagination_kalshi_historical_data("KXSOL15M")
fetch_pagination_kalshi_current_data("KXSOL15M")
# # XRP
fetch_pagination_kalshi_historical_data("KXXRP15M")
fetch_pagination_kalshi_current_data("KXXRP15M")
# OIL
fetch_pagination_kalshi_historical_data("KXWTI15M")
fetch_pagination_kalshi_current_data("KXWTI15M")


merge("KXBNB15M")
merge("KXBTC15M")
merge("KXDOGE15M")
merge("KXETH15M")
merge("KXGOLD15M")
merge("KXHYPE15M")
merge("KXSILVER15M")
merge("KXSOL15M")
merge("KXXRP15M")
merge("KXWTI15M")

sort_by_event_ticker("KXBNB15M")
sort_by_event_ticker("KXBTC15M")
sort_by_event_ticker("KXDOGE15M")
sort_by_event_ticker("KXETH15M")
sort_by_event_ticker("KXGOLD15M")
sort_by_event_ticker("KXHYPE15M")
sort_by_event_ticker("KXSILVER15M")
sort_by_event_ticker("KXSOL15M")
sort_by_event_ticker("KXXRP15M")
sort_by_event_ticker("KXWTI15M")

# fetch_and_save_kalshi_paging("KXBTC15M")