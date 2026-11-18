import pandas as pd

from strategies.market_structure import detect_swings


# Load validated Gold M15 data
df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv"
)

# Convert time column
df["time"] = pd.to_datetime(
    df["time"]
)

# Detect swings
df = detect_swings(
    df,
    lookback=5
)

# Keep only candles where a swing was detected
swings = df[
    (df["swing_high"] == True)
    |
    (df["swing_low"] == True)
]


print("\n======================================")
print("SWING DETECTION RESULTS")
print("======================================")

print(
    f"Total candles: {len(df):,}"
)

print(
    f"Swing highs: {df['swing_high'].sum():,}"
)

print(
    f"Swing lows: {df['swing_low'].sum():,}"
)

print(
    f"Total swings: {len(swings):,}"
)

print("\nLast 30 detected swings:")

print(
    swings[
        [
            "time",
            "high",
            "low",
            "swing_high",
            "swing_low"
        ]
    ].tail(30).to_string(
        index=False
    )
)

# ============================================================
# ANALYZE DISTANCE BETWEEN SWINGS
# ============================================================

swings = df[
    (df["swing_high"] == True)
    |
    (df["swing_low"] == True)
].copy()

swings["price"] = swings.apply(
    lambda row:
        row["high"]
        if row["swing_high"]
        else row["low"],
    axis=1
)

swings["price_distance"] = (
    swings["price"].diff().abs()
)

swings["bars_between"] = (
    swings.index.to_series().diff()
)


print("\n======================================")
print("SWING SPACING ANALYSIS")
print("======================================")

print(
    "\nAverage price distance:",
    swings["price_distance"].mean()
)

print(
    "Median price distance:",
    swings["price_distance"].median()
)

print(
    "Minimum price distance:",
    swings["price_distance"].min()
)

print(
    "\nAverage bars between swings:",
    swings["bars_between"].mean()
)

print(
    "Median bars between swings:",
    swings["bars_between"].median()
)

print(
    "Minimum bars between swings:",
    swings["bars_between"].min()
)

# ============================================================
# ATR-BASED SWING ANALYSIS
# ============================================================

import numpy as np

# Calculate True Range

previous_close = df["close"].shift(1)

tr1 = df["high"] - df["low"]

tr2 = (
    df["high"] - previous_close
).abs()

tr3 = (
    df["low"] - previous_close
).abs()

df["true_range"] = pd.concat(
    [tr1, tr2, tr3],
    axis=1
).max(axis=1)

# Calculate ATR

df["atr"] = df["true_range"].rolling(14).mean()


# ============================================================
# PREPARE SWING DATA
# ============================================================

swings = df[
    (df["swing_high"]) |
    (df["swing_low"])
].copy()

swings["swing_type"] = np.where(
    swings["swing_high"],
    "HIGH",
    "LOW"
)

swings["swing_price"] = np.where(
    swings["swing_high"],
    swings["high"],
    swings["low"]
)

# Calculate distance between consecutive swings

swings["price_distance"] = (
    swings["swing_price"].diff().abs()
)

# Calculate ATR-normalized movement

swings["atr_multiple"] = (
    swings["price_distance"] / swings["atr"]
)


# ============================================================
# DIAGNOSTICS
# ============================================================

print("\n======================================")
print("ATR SWING ANALYSIS")
print("======================================")

print(
    "\nMedian ATR:",
    df["atr"].median()
)

print(
    "Average ATR:",
    df["atr"].mean()
)

print(
    "\nMedian swing distance:",
    swings["price_distance"].median()
)

print(
    "Median ATR multiple:",
    swings["atr_multiple"].median()
)

print(
    "\nSwings below 0.5 ATR:",
    (swings["atr_multiple"] < 0.5).sum()
)

print(
    "Swings between 0.5 and 1 ATR:",
    (
        (swings["atr_multiple"] >= 0.5) &
        (swings["atr_multiple"] < 1)
    ).sum()
)

print(
    "Swings between 1 and 2 ATR:",
    (
        (swings["atr_multiple"] >= 1) &
        (swings["atr_multiple"] < 2)
    ).sum()
)

print(
    "Swings above 2 ATR:",
    (swings["atr_multiple"] >= 2).sum()
)


# ============================================================
# CONSECUTIVE SWING ANALYSIS
# ============================================================

same_type = (
    swings["swing_type"] ==
    swings["swing_type"].shift(1)
)

print(
    "\nConsecutive swing highs/lows:",
    same_type.sum()
)

print(
    "\nZero-distance swings:",
    (swings["price_distance"] == 0).sum()
)

print("\nLast 15 swing observations:")

print(
    swings[
        [
            "time",
            "swing_type",
            "swing_price",
            "atr",
            "price_distance",
            "atr_multiple"
        ]
    ].tail(15).to_string(index=False)
)

# ======================================
# SWING DETECTOR AUDIT
# ======================================

print("\n======================================")
print("SWING DETECTOR AUDIT")
print("======================================")

# 1. Candles classified as both swing high and swing low
both_swings = df[
    (df["swing_high"]) &
    (df["swing_low"])
]

print("\nCandles classified as BOTH:")
print(len(both_swings))

if len(both_swings) > 0:
    print(both_swings[
        ["time", "high", "low"]
    ].head(10).to_string(index=False))


# 2. Consecutive swing types
swings = df[
    (df["swing_high"]) |
    (df["swing_low"])
].copy()

swings["swing_type"] = np.where(
    swings["swing_high"],
    "HIGH",
    "LOW"
)

same_type = (
    swings["swing_type"] ==
    swings["swing_type"].shift(1)
)

print("\nConsecutive swing types:")
print(same_type.sum())

print("\nExamples of consecutive swing types:")

print(
    swings.loc[same_type, [
        "time",
        "high",
        "low",
        "swing_type"
    ]].head(15).to_string(index=False)
)


# 3. Zero-distance observations
swings["swing_price"] = np.where(
    swings["swing_high"],
    swings["high"],
    swings["low"]
)

swings["price_distance"] = (
    swings["swing_price"].diff().abs()
)

zero_distance = swings[
    swings["price_distance"] == 0
]

print("\nZero-distance swings:")
print(len(zero_distance))

if len(zero_distance) > 0:
    print(zero_distance[
        ["time", "swing_type", "swing_price"]
    ].to_string(index=False))


# 4. Swing type distribution
print("\nSwing type distribution:")
print(swings["swing_type"].value_counts())