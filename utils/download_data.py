print("=== DOWNLOAD_DATA.PY STARTED ===")
from datetime import datetime
import os

import MetaTrader5 as mt5
import pandas as pd

from config.settings import SYMBOL, TIMEFRAMES, START_YEAR


def connect_mt5():

    if not mt5.initialize():
        raise Exception("MetaTrader5 failed to initialize.")

    print("Connected to MetaTrader 5")


def download(symbol, timeframe_name, timeframe):

    print(f"\nTesting {symbol} {timeframe_name}...")

    # Make sure the symbol is selected
    if not mt5.symbol_select(symbol, True):
        print("Failed to select symbol")
        return

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        10
    )

    print("MT5 Last Error:", mt5.last_error())

    if rates is None:
        print("No data returned.")
        return

    print(f"Received {len(rates)} candles")

    df = pd.DataFrame(rates)

    print(df.head())


def main():

    print("Entered main()")

    connect_mt5()

    print(mt5.terminal_info())
    print(mt5.account_info())

    symbols = mt5.symbols_get()

    print(f"Found {len(symbols)} symbols")

    print("\nAvailable Gold Symbols:")

    for s in symbols:
        if "XAU" in s.name.upper() or "GOLD" in s.name.upper():
            print("-", s.name)

    print("\nStarting download...\n")

    for tf_name, tf in TIMEFRAMES.items():
        download(SYMBOL, tf_name, tf)

    mt5.shutdown()

    print("\nDone.")

if __name__ == "__main__":
    main()