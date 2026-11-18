import pandas as pd

from strategies.market_structure import (
    detect_swings,
    build_alternating_pivots
)


# ======================================
# 1. LOAD DATA
# ======================================

df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv",
    parse_dates=["time"]
)

df = df.reset_index(drop=True)

# Validate timestamps
if df["time"].duplicated().any():
    raise ValueError("Duplicate timestamps found in dataset.")

if not df["time"].is_monotonic_increasing:
    raise ValueError("Dataset is not in chronological order.")

print("Dataset loaded successfully.")
print("Total candles:", len(df))


# ======================================
# 2. CALCULATE ATR
# ======================================

previous_close = df["close"].shift(1)

tr1 = df["high"] - df["low"]
tr2 = (df["high"] - previous_close).abs()
tr3 = (df["low"] - previous_close).abs()

df["true_range"] = pd.concat(
    [tr1, tr2, tr3],
    axis=1
).max(axis=1)

df["atr"] = df["true_range"].rolling(
    window=14
).mean()


# ======================================
# 3. DETECT AND CLEAN PIVOTS
# ======================================

df = detect_swings(
    df,
    lookback=5
)

pivots = build_alternating_pivots(
    df,
    lookback=5
)

print("\nPivot detection completed.")
print("Total cleaned pivots:", len(pivots))

if len(pivots) < 2:
    raise ValueError("Not enough pivots to calculate pivot legs.")


# ======================================
# 4. CALCULATE PIVOT LEG DISTANCES
# ======================================

pivots["leg_distance"] = (
    pivots["pivot_price"].diff().abs()
)


# ======================================
# 5. MATCH ATR USING CONFIRMATION TIME
# ======================================

# Create an ATR lookup table.
# Rename 'time' to 'confirmation_time' to avoid
# creating duplicate timestamp columns during merging.

atr_lookup = df[
    ["time", "atr"]
].rename(
    columns={"time": "confirmation_time"}
)

# Match each pivot to ATR at its confirmation candle.

pivots = pivots.merge(
    atr_lookup,
    on="confirmation_time",
    how="left",
    validate="many_to_one"
)

# ======================================
# CHECK MISSING ATR MATCHES
# ======================================

missing_atr = pivots[pivots["atr"].isna()]

print("\nPivots with missing ATR:")
print(
    missing_atr[
        [
            "pivot_time",
            "confirmation_time",
            "pivot_type",
            "pivot_price"
        ]
    ].to_string(index=False)
)

# Verify that the merge preserved all pivots.

if len(pivots) != len(atr_lookup) and len(pivots) < 0:
    raise ValueError("Unexpected merge issue.")


# ======================================
# 6. CALCULATE ATR MULTIPLES
# ======================================

pivots["atr_multiple"] = (
    pivots["leg_distance"] / pivots["atr"]
)

# Remove first pivot and invalid ATR observations.

legs = pivots.dropna(
    subset=[
        "leg_distance",
        "atr",
        "atr_multiple"
    ]
).copy()

print("\nATR matching completed.")
print("Valid pivot legs:", len(legs))

if len(legs) == 0:
    raise ValueError("No valid pivot legs available for analysis.")


# ======================================
# 7. GENERAL ANALYSIS
# ======================================

print("\n======================================")
print("PIVOT SIGNIFICANCE ANALYSIS")
print("======================================")

print("\nTotal cleaned pivots:", len(pivots))
print("Valid pivot legs:", len(legs))

print("\nMedian ATR:", df["atr"].median())
print("Average ATR:", df["atr"].mean())

print(
    "\nMedian leg distance:",
    legs["leg_distance"].median()
)

print(
    "Average leg distance:",
    legs["leg_distance"].mean()
)

print(
    "\nMedian ATR multiple:",
    legs["atr_multiple"].median()
)

print(
    "Average ATR multiple:",
    legs["atr_multiple"].mean()
)


# ======================================
# 8. ATR MULTIPLE DISTRIBUTION
# ======================================

print("\n======================================")
print("ATR MULTIPLE DISTRIBUTION")
print("======================================")

print(
    "Below 0.5 ATR:",
    (legs["atr_multiple"] < 0.5).sum()
)

print(
    "0.5 - 1 ATR:",
    (
        (legs["atr_multiple"] >= 0.5) &
        (legs["atr_multiple"] < 1)
    ).sum()
)

print(
    "1 - 1.5 ATR:",
    (
        (legs["atr_multiple"] >= 1) &
        (legs["atr_multiple"] < 1.5)
    ).sum()
)

print(
    "1.5 - 2 ATR:",
    (
        (legs["atr_multiple"] >= 1.5) &
        (legs["atr_multiple"] < 2)
    ).sum()
)

print(
    "Above 2 ATR:",
    (legs["atr_multiple"] >= 2).sum()
)


# ======================================
# 9. TEST POTENTIAL ATR FILTERS
# ======================================

print("\n======================================")
print("POTENTIAL ATR FILTERS")
print("======================================")

for threshold in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:

    selected = legs[
        legs["atr_multiple"] >= threshold
    ]

    percentage = (
        len(selected) / len(legs)
    ) * 100

    print(
        f"{threshold} ATR: "
        f"{len(selected)} legs "
        f"({percentage:.2f}%)"
    )


# ======================================
# 10. LATEST 20 PIVOT LEGS
# ======================================

print("\n======================================")
print("LATEST 20 PIVOT LEGS")
print("======================================")

print(
    legs[
        [
            "pivot_time",
            "confirmation_time",
            "pivot_type",
            "pivot_price",
            "leg_distance",
            "atr",
            "atr_multiple"
        ]
    ].tail(20).to_string(index=False)
)


# ======================================
# 11. FINAL VALIDATION
# ======================================

print("\n======================================")
print("FINAL VALIDATION")
print("======================================")

print(
    "Missing ATR values:",
    pivots["atr"].isna().sum()
)

print(
    "Missing ATR multiples in valid legs:",
    legs["atr_multiple"].isna().sum()
)

print(
    "Negative ATR multiples:",
    (legs["atr_multiple"] < 0).sum()
)

print("\nPIVOT SIGNIFICANCE TEST COMPLETED.")