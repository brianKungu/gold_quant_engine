import pandas as pd
from pathlib import Path

from config.settings import (
    ATR_PERIOD,
    ATR_MULTIPLIER
)

from strategies.market_structure import (
    detect_atr_zigzag
)

from strategies.structure_classifier import (
    classify_market_structure
)

from strategies.protected_levels import (
    identify_protected_levels
)

from strategies.structure_breaks import (
    detect_structure_breaks
)


# ======================================
# 1. LOAD HISTORICAL DATA
# ======================================

DATA_PATH = Path("data/raw/XAUUSD_M15.csv")

df = pd.read_csv(
    DATA_PATH,
    parse_dates=["time"]
)

df = df.reset_index(drop=True)

print("\n======================================")
print("GOLD HISTORICAL STRUCTURE ANALYSIS")
print("======================================")

print("Dataset loaded:", len(df), "candles")

if df.empty:
    raise ValueError("Historical dataset is empty.")

if df["time"].duplicated().any():
    raise ValueError("Duplicate timestamps detected.")

if not df["time"].is_monotonic_increasing:
    raise ValueError("Dataset is not chronological.")

print("First candle:", df["time"].iloc[0])
print("Last candle:", df["time"].iloc[-1])


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
    window=ATR_PERIOD
).mean()

print("\nATR calculated.")

print("ATR period:", ATR_PERIOD)
print("ATR multiplier:", ATR_MULTIPLIER)
print("Median ATR:", df["atr"].median())


# ======================================
# 3. DETECT ATR ZIGZAG PIVOTS
# ======================================

pivots = detect_atr_zigzag(
    df,
    atr_column="atr",
    multiplier=ATR_MULTIPLIER
)

print("\nZigZag detection completed.")

print("Total pivots:", len(pivots))

if pivots.empty:
    raise ValueError("No pivots detected.")


# ======================================
# 4. CLASSIFY MARKET STRUCTURE
# ======================================

classified = classify_market_structure(
    pivots
)

print("\nMarket structure classification completed.")

print("\nSTRUCTURE DISTRIBUTION")

print(
    classified["structure"].value_counts()
)


# ======================================
# 5. IDENTIFY PROTECTED LEVELS
# ======================================

protected = identify_protected_levels(
    classified
)

print("\nProtected-level identification completed.")

print("\nSTRUCTURAL DIRECTION DISTRIBUTION")

print(
    protected["structure_direction"].value_counts()
)


# ======================================
# 6. DETECT BOS AND CHOCH
# ======================================

events = detect_structure_breaks(
    candles=df,
    protected_pivots=protected
)

print("\nStructural break detection completed.")

print("Total structural events:", len(events))


# ======================================
# 7. EVENT DISTRIBUTION
# ======================================

print("\n======================================")
print("BOS / CHOCH EVENT DISTRIBUTION")
print("======================================")

if events.empty:

    print("No structural break events detected.")

else:

    event_counts = events["event_type"].value_counts()

    print(event_counts)

    print("\nEVENT PERCENTAGES")

    print(
        (
            events["event_type"].value_counts(normalize=True)
            * 100
        ).round(2)
    )


# ======================================
# 8. YEARLY EVENT DISTRIBUTION
# ======================================

print("\n======================================")
print("YEARLY EVENT DISTRIBUTION")
print("======================================")

if not events.empty:

    events["year"] = (
        pd.to_datetime(events["event_time"]).dt.year
    )

    yearly = pd.crosstab(
        events["year"],
        events["event_type"]
    )

    print(yearly)


# ======================================
# 9. EVENT FREQUENCY
# ======================================

print("\n======================================")
print("EVENT FREQUENCY")
print("======================================")

if not events.empty:

    first_date = df["time"].iloc[0]

    last_date = df["time"].iloc[-1]

    days = (
        last_date - first_date
    ).total_seconds() / 86400

    print("Dataset duration:", round(days, 2), "days")

    print(
        "Average events per 30 days:",
        round(len(events) / days * 30, 2)
    )

    print("\nEvents by type:")

    for event_type, count in events["event_type"].value_counts().items():

        print(
            f"{event_type}: {count} "
            f"({count / days * 30:.2f} per 30 days)"
        )


# ======================================
# 10. LATEST 30 EVENTS
# ======================================

print("\n======================================")
print("LATEST 30 STRUCTURAL EVENTS")
print("======================================")

if not events.empty:

    print(
        events.tail(30).to_string(index=False)
    )


# ======================================
# 11. VALIDATION
# ======================================

print("\n======================================")
print("FINAL VALIDATION")
print("======================================")

print(
    "Missing event types:",
    events["event_type"].isna().sum()
)

print(
    "Chronological event order:",
    events["event_time"].is_monotonic_increasing
)

print(
    "Invalid event candle indices:",
    (
        (events["candle_index"] < 0) |
        (events["candle_index"] >= len(df))
    ).sum()
)

print(
    "Invalid execution indices:",
    (
        events["earliest_execution_index"]
        != events["candle_index"] + 1
    ).sum()
)

print(
    "Events with missing broken levels:",
    events["broken_level_price"].isna().sum()
)

print(
    "Duplicate broken-level events:",
    events.duplicated(
        subset=[
            "event_type",
            "broken_level_type",
            "level_confirmation_index"
        ]
    ).sum()
)


# ======================================
# 12. EXPORT RESULTS
# ======================================

output_directory = Path("backtests")

output_directory.mkdir(
    parents=True,
    exist_ok=True
)

output_file = (
    output_directory /
    "historical_structure_events.csv"
)

events.to_csv(
    output_file,
    index=False
)

print("\nHistorical event report saved to:")

print(output_file)

print("\nHISTORICAL STRUCTURE ANALYSIS COMPLETED.")