import pandas as pd

from strategies.market_structure import detect_atr_zigzag
from strategies.structure_classifier import classify_market_structure
from config.settings import (ATR_MULTIPLIER, ATR_PERIOD)
# ======================================
# 1. LOAD DATA
# ======================================

df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv",
    parse_dates=["time"]
)

df = df.reset_index(drop=True)

print("Dataset loaded:", len(df))


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

df["atr"] = df["true_range"].rolling(window=ATR_PERIOD
).mean()


# ======================================
# 3. DETECT ZIGZAG PIVOTS
# ======================================

pivots = detect_atr_zigzag(
    df,
    atr_column="atr",
    multiplier=ATR_MULTIPLIER
)

print("\nZigZag detection completed.")
print("Total pivots:", len(pivots))


# ======================================
# 4. CLASSIFY MARKET STRUCTURE
# ======================================

structure = classify_market_structure(pivots)

print("\nMarket structure classification completed.")


# ======================================
# 5. STRUCTURE DISTRIBUTION
# ======================================

print("\n===================================")
print("STRUCTURE DISTRIBUTION")
print("===================================")

print(
    structure["structure"]
    .value_counts()
    .to_string()
)


# ======================================
# 6. TREND DISTRIBUTION
# ======================================

print("\n===================================")
print("TREND DISTRIBUTION")
print("===================================")

print(
    structure["trend_state"]
    .value_counts()
    .to_string()
)


# ======================================
# 7. YEARLY TREND DISTRIBUTION
# ======================================

structure["year"] = pd.to_datetime(
    structure["confirmation_time"]
).dt.year

yearly = pd.crosstab(
    structure["year"],
    structure["trend_state"]
)

print("\n===================================")
print("YEARLY TREND DISTRIBUTION")
print("===================================")

print(yearly.to_string())


# ======================================
# 8. LATEST 30 CLASSIFIED PIVOTS
# ======================================

print("\n===================================")
print("LATEST 30 MARKET STRUCTURE EVENTS")
print("===================================")

print(
    structure[
        [
            "pivot_time",
            "confirmation_time",
            "pivot_type",
            "pivot_price",
            "structure",
            "trend_state"
        ]
    ].tail(30).to_string(index=False)
)


# ======================================
# 9. VALIDATION
# ======================================

print("\n===================================")
print("VALIDATION")
print("===================================")

print(
    "Missing structure labels:",
    structure["structure"].isna().sum()
)

print(
    "Missing trend states:",
    structure["trend_state"].isna().sum()
)

print(
    "Duplicate confirmation indices:",
    structure["confirmation_index"].duplicated().sum()
)

print(
    "Chronological confirmation order:",
    structure["confirmation_index"].is_monotonic_increasing
)

print("\nMARKET STRUCTURE TEST COMPLETED.")