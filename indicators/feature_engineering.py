import pandas as pd

from ta.trend import EMAIndicator
from ta.trend import ADXIndicator
from ta.trend import MACD

from ta.momentum import RSIIndicator

from ta.volatility import AverageTrueRange
from ta.volatility import BollingerBands


def create_features(df):

    # Trend

    # ==========================
    # EMA
    # ==========================

    df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()

    df["ema50"] = EMAIndicator(df["close"], window=50).ema_indicator()

    df["ema200"] = EMAIndicator(df["close"], window=200).ema_indicator()

    # ==========================
    # EMA Slope
    # ==========================

    df["ema50_slope"] = (
        df["ema50"] -
        df["ema50"].shift(5)
    )

    # Momentum

    df["rsi"] = RSIIndicator(
            df["close"],
            window=14
    ).rsi()

    macd = MACD(df["close"])

    df["macd"] = macd.macd()

    df["macd_signal"] = macd.macd_signal()

    df["macd_hist"] = macd.macd_diff()
    # Volatility
    atr = AverageTrueRange(
    high=df["high"],
    low=df["low"],
    close=df["close"],
    window=14
    )

    df["atr"] = atr.average_true_range()

    df["atr_mean"] = (
        df["atr"]
        .rolling(50)
        .mean()
    )

    df["high_volatility"] = (
        df["atr"] >
        df["atr_mean"]
    )

    df["adx"] = adx.adx()
    adx = ADXIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )
    bb = BollingerBands(
        df["close"],
        window=20
    )

    df["bb_upper"] = bb.bollinger_hband()

    df["bb_lower"] = bb.bollinger_lband()

    df["bb_width"] = bb.bollinger_wband()
    # Candle Features
    
    df["body"] = abs(
    df["close"] -
    df["open"]
    )

    df["range"] = (
        df["high"] -
        df["low"]
    )

    df["upper_wick"] = (
        df["high"] -
        df[["open", "close"]].max(axis=1)
    )

    df["lower_wick"] = (
        df[["open", "close"]].min(axis=1) -
        df["low"]
    )

    df["body_percent"] = (
        df["body"] /
        df["range"]
    )
    # Time Features
    df["hour"] = df["time"].dt.hour

    df["weekday"] = df["time"].dt.weekday

    df["month"] = df["time"].dt.month

    # session features
    df["asian_session"] = (
        (df["hour"] >= 0) &
        (df["hour"] < 8)
    )

    df["london_session"] = (
        (df["hour"] >= 8) &
        (df["hour"] < 16)
    )

    df["newyork_session"] = (
        (df["hour"] >= 13) &
        (df["hour"] < 21)
    )

    return df