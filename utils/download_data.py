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
    Download historical OHLC data using MT5's position-based method.

    This requests a large number of the most recent candles rather
    than passing a date range to MT5. This is more compatible with
    different MT5 broker terminals.
    """

    print(f"\nDownloading {symbol} {timeframe_name}...")

    # Make sure the symbol is available in Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select symbol: {symbol}")
        print("MT5 Error:", mt5.last_error())
        return None

    # --------------------------------------------------------
    # Number of candles to request
    # --------------------------------------------------------
    #
    # M15:
    # 100,000 candles ≈ 1,041 days
    #
    # H1:
    # 100,000 candles ≈ 11 years
    #
    # H4:
    # 100,000 candles ≈ 45 years
    #
    # We will later build a proper chunked downloader if we
    # need more M15 history.
    # --------------------------------------------------------

    bars_to_download = 1000

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        bars_to_download
    )

    print("MT5 Error:", mt5.last_error())

    if rates is None:

        print(
            f"No data received for {symbol} {timeframe_name}"
        )

        return None

    if len(rates) == 0:

        print(
            f"MT5 returned zero candles for {symbol} {timeframe_name}"
        )

        return None

    # Convert to DataFrame
    df = pd.DataFrame(rates)

    # Convert Unix timestamp to datetime
    df["time"] = pd.to_datetime(
        df["time"],
        unit="s"
    )

    # Sort oldest → newest
    df.sort_values(
        "time",
        inplace=True
    )

    # Remove duplicate timestamps
    df.drop_duplicates(
        subset="time",
        keep="first",
        inplace=True
    )

    # Reset index
    df.reset_index(
        drop=True,
        inplace=True
    )

    # Create directory
    output_directory = "data/raw"

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    # Create filename
    filename = os.path.join(
        output_directory,
        f"{symbol}_{timeframe_name}.csv"
    )

    # Save
    df.to_csv(
        filename,
        index=False
    )

    # Report
    print(
        f"Saved: {filename}"
    )

    print(
        f"Candles downloaded: {len(df):,}"
    )

    print(
        f"First candle: {df['time'].iloc[0]}"
    )

    print(
        f"Last candle: {df['time'].iloc[-1]}"
    )

    print(
        f"Columns: {list(df.columns)}"
    )

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