import pandas as pd


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv"
)

df["time"] = pd.to_datetime(
    df["time"]
)


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\n======================================")
print("XAUUSD M15 DATA QUALITY CHECK")
print("======================================")

print(
    f"Rows: {len(df):,}"
)

print(
    f"Columns: {len(df.columns)}"
)

print(
    f"First candle: {df['time'].iloc[0]}"
)

print(
    f"Last candle: {df['time'].iloc[-1]}"
)


# ============================================================
# CHECK 1 — DUPLICATES
# ============================================================

duplicates = df["time"].duplicated().sum()

print("\nDuplicate timestamps:", duplicates)


# ============================================================
# CHECK 2 — CHRONOLOGICAL ORDER
# ============================================================

is_sorted = df["time"].is_monotonic_increasing

print(
    "Chronologically ordered:",
    is_sorted
)


# ============================================================
# CHECK 3 — MISSING VALUES
# ============================================================

missing_values = df[
    [
        "open",
        "high",
        "low",
        "close"
    ]
].isna().sum()

print("\nMissing OHLC values:")
print(missing_values)


# ============================================================
# CHECK 4 — PRICE VALIDITY
# ============================================================

invalid_high = (
    df["high"] <
    df[["open", "close"]].max(axis=1)
).sum()

invalid_low = (
    df["low"] >
    df[["open", "close"]].min(axis=1)
).sum()

print(
    "\nInvalid high values:",
    invalid_high
)

print(
    "Invalid low values:",
    invalid_low
)


# ============================================================
# CHECK 5 — ZERO / NEGATIVE PRICES
# ============================================================

invalid_prices = (
    df[
        [
            "open",
            "high",
            "low",
            "close"
        ]
    ] <= 0
).sum().sum()

print(
    "Zero/negative prices:",
    invalid_prices
)


# ============================================================
# FINAL RESULT
# ============================================================

print("\n======================================")

if (
    duplicates == 0
    and is_sorted
    and missing_values.sum() == 0
    and invalid_high == 0
    and invalid_low == 0
    and invalid_prices == 0
):

    print("DATA QUALITY: PASSED")

else:

    print("DATA QUALITY: FAILED")

print("======================================")