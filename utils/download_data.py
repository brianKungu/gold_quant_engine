"""
download_data.py

Gold Quant Engine - Historical Data Downloader

Purpose:
--------
Connects to MetaTrader 5, downloads historical XAUUSD data
for the configured timeframes, validates the basic response,
and saves the data into:

    data/raw/

The raw data is intentionally kept untouched because all
feature engineering and strategy calculations should happen
later in the pipeline.
"""

from datetime import datetime
import os

import MetaTrader5 as mt5
import pandas as pd

from config.settings import SYMBOL, TIMEFRAMES, START_YEAR


# ============================================================
# MT5 CONNECTION
# ============================================================

def connect_mt5():
    """
    Connect to the currently installed MetaTrader 5 terminal.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If MetaTrader 5 cannot be initialized.
    """

    if not mt5.initialize():
        raise RuntimeError(
            f"MetaTrader 5 initialization failed: {mt5.last_error()}"
        )

    print("Connected to MetaTrader 5")


# ============================================================
# DOWNLOAD DATA
# ============================================================

def download(symbol, timeframe_name, timeframe):
    """
    Download historical OHLC data from MetaTrader 5 in chunks.

    MT5's terminal/broker is currently rejecting large requests,
    so we request 1,000 candles at a time and work backwards.

    The chunks are then combined into one dataset.

    Parameters
    ----------
    symbol : str
        MT5 symbol, e.g. XAUUSD.

    timeframe_name : str
        Human-readable timeframe, e.g. M15.

    timeframe :
        MT5 timeframe constant.

    Returns
    -------
    pandas.DataFrame
        Combined historical dataset.
    """

    print(f"\nDownloading {symbol} {timeframe_name}...")

    # --------------------------------------------------------
    # Make sure the symbol is available
    # --------------------------------------------------------

    if not mt5.symbol_select(symbol, True):

        print(f"Failed to select {symbol}")
        print("MT5 Error:", mt5.last_error())

        return None

    # --------------------------------------------------------
    # Maximum number of candles requested per MT5 call
    # --------------------------------------------------------

    CHUNK_SIZE = 1000

    # --------------------------------------------------------
    # Number of chunks we want.
    #
    # 100 chunks × 1,000 candles = up to 100,000 candles.
    #
    # We will later make this configurable.
    # --------------------------------------------------------

    MAX_CHUNKS = 100

    all_data = []

    # MT5 position 0 represents the most recent candle.
    #
    # We start from the latest candle and move backwards.
    start_pos = 0

    # --------------------------------------------------------
    # Download chunks
    # --------------------------------------------------------

    for chunk_number in range(MAX_CHUNKS):

        print(
            f"Downloading chunk "
            f"{chunk_number + 1}/{MAX_CHUNKS}..."
        )

        rates = mt5.copy_rates_from_pos(
            symbol,
            timeframe,
            start_pos,
            CHUNK_SIZE
        )

        # ----------------------------------------------------
        # Check for errors
        # ----------------------------------------------------

        if rates is None:

            print(
                f"MT5 returned no data at position "
                f"{start_pos}"
            )

            print(
                "MT5 Error:",
                mt5.last_error()
            )

            break

        # ----------------------------------------------------
        # Stop if MT5 returns no candles
        # ----------------------------------------------------

        if len(rates) == 0:

            print("No more historical data available.")

            break

        # ----------------------------------------------------
        # Convert to DataFrame
        # ----------------------------------------------------

        chunk = pd.DataFrame(rates)

        # Convert Unix timestamp
        chunk["time"] = pd.to_datetime(
            chunk["time"],
            unit="s"
        )

        # Add chunk
        all_data.append(chunk)

        print(
            f"Received {len(chunk)} candles | "
            f"{chunk['time'].min()} → "
            f"{chunk['time'].max()}"
        )

        # ----------------------------------------------------
        # If fewer than CHUNK_SIZE were returned, we have
        # reached the available historical data.
        # ----------------------------------------------------

        if len(chunk) < CHUNK_SIZE:

            print(
                "Reached available historical data."
            )

            break

        # ----------------------------------------------------
        # Move backwards by another chunk.
        # ----------------------------------------------------

        start_pos += CHUNK_SIZE

    # --------------------------------------------------------
    # Make sure something was downloaded
    # --------------------------------------------------------

    if not all_data:

        print(
            f"No historical data downloaded for "
            f"{symbol} {timeframe_name}"
        )

        return None

    # --------------------------------------------------------
    # Combine all chunks
    # --------------------------------------------------------

    df = pd.concat(
        all_data,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Sort oldest → newest
    # --------------------------------------------------------

    df.sort_values(
        "time",
        inplace=True
    )

    # --------------------------------------------------------
    # Remove duplicate timestamps
    # --------------------------------------------------------

    df.drop_duplicates(
        subset="time",
        keep="first",
        inplace=True
    )

    # --------------------------------------------------------
    # Reset index
    # --------------------------------------------------------

    df.reset_index(
        drop=True,
        inplace=True
    )

    # --------------------------------------------------------
    # Save raw data
    # --------------------------------------------------------

    output_directory = "data/raw"

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    filename = os.path.join(
        output_directory,
        f"{symbol}_{timeframe_name}.csv"
    )

    df.to_csv(
        filename,
        index=False
    )

    # --------------------------------------------------------
    # Report final dataset
    # --------------------------------------------------------

    print("\n------------------------------------------")

    print(
        f"Saved: {filename}"
    )

    print(
        f"Total candles: {len(df):,}"
    )

    print(
        f"First candle: {df['time'].iloc[0]}"
    )

    print(
        f"Last candle: {df['time'].iloc[-1]}"
    )

    print("------------------------------------------")

    return df
# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    """
    Main execution function.

    Connects to MT5, downloads every timeframe defined in
    config/settings.py, saves each dataset, then disconnects.
    """

    print(
        "=========================================="
    )

    print(
        "       GOLD QUANT ENGINE"
    )

    print(
        "       HISTORICAL DATA DOWNLOAD"
    )

    print(
        "=========================================="
    )

    # --------------------------------------------------------
    # Connect to MetaTrader 5
    # --------------------------------------------------------

    connect_mt5()

    # --------------------------------------------------------
    # Display terminal/account information
    # --------------------------------------------------------

    print("\nMT5 Terminal:")

    print(
        mt5.terminal_info()
    )

    print("\nMT5 Account:")

    print(
        mt5.account_info()
    )

    # --------------------------------------------------------
    # Verify configured symbol
    # --------------------------------------------------------

    print(
        f"\nConfigured symbol: {SYMBOL}"
    )

    # --------------------------------------------------------
    # Download every configured timeframe
    # --------------------------------------------------------

    print(
        "\nStarting historical data download..."
    )

    for timeframe_name, timeframe in TIMEFRAMES.items():

        download(
            SYMBOL,
            timeframe_name,
            timeframe
        )

    # --------------------------------------------------------
    # Disconnect from MT5
    # --------------------------------------------------------

    mt5.shutdown()

    print(
        "\n=========================================="
    )

    print(
        "Download complete."
    )

    print(
        "=========================================="
    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()