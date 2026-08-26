"""
market_structure.py

Purpose:
--------
This module identifies the market's structural turning points.

Rather than relying on lagging indicators, it detects:

- Swing Highs
- Swing Lows

These swings become the foundation for:

- Higher Highs (HH)
- Higher Lows (HL)
- Lower Highs (LH)
- Lower Lows (LL)
- Break of Structure (BOS)
- Change of Character (CHOCH)

Author:
Gold Quant Engine
"""

import pandas as pd


def detect_swings(df, lookback=5):
    """
    Detect confirmed swing highs and swing lows.

    Parameters
    ----------
    df : pandas.DataFrame
        Price dataframe containing:
        High
        Low

    lookback : int
        Number of candles on BOTH sides used
        to confirm a swing.

    Returns
    -------
    pandas.DataFrame
        Original dataframe with:

        swing_high
        swing_low
    """

    df = df.copy()

    df["swing_high"] = False
    df["swing_low"] = False

    for i in range(lookback, len(df) - lookback):

        high = df["high"].iloc[i]
        low = df["low"].iloc[i]

        left_high = df["high"].iloc[i-lookback:i]
        right_high = df["high"].iloc[i+1:i+lookback+1]

        left_low = df["low"].iloc[i-lookback:i]
        right_low = df["low"].iloc[i+1:i+lookback+1]

        if (
            high > left_high.max()
            and
            high > right_high.max()
        ):
            df.loc[df.index[i], "swing_high"] = True

        if (
            low < left_low.min()
            and
            low < right_low.min()
        ):
            df.loc[df.index[i], "swing_low"] = True

    return df