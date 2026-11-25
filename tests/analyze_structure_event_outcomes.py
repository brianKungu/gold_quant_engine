import pandas as pd
import numpy as np
from pathlib import Path


# ======================================
# 1. CONFIGURATION
# ======================================

DATA_FILE = Path("data/raw/XAUUSD_M15.csv")

EVENT_FILE = Path(
    "backtests/historical_structure_events.csv"
)

OUTPUT_DIRECTORY = Path("backtests")

HORIZONS = [4, 8, 16, 32]


# ======================================
# 2. LOAD DATA
# ======================================

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["time"]
)

events = pd.read_csv(
    EVENT_FILE,
    parse_dates=["event_time"]
)

df = df.reset_index(drop=True)
events = events.reset_index(drop=True)

print("\n======================================")
print("STRUCTURAL EVENT OUTCOME ANALYSIS")
print("======================================")

print("Historical candles:", len(df))
print("Historical events:", len(events))

if df["time"].duplicated().any():
    raise ValueError("Duplicate candle timestamps.")

if not df["time"].is_monotonic_increasing:
    raise ValueError("Candles are not chronological.")

if events.empty:
    raise ValueError("No historical events found.")


# ======================================
# 3. DEFINE EVENT DIRECTION
# ======================================

direction_map = {

    "BULLISH_BOS": 1,

    "BULLISH_CHOCH": 1,

    "BEARISH_BOS": -1,

    "BEARISH_CHOCH": -1

}

events["direction"] = events["event_type"].map(
    direction_map
)

if events["direction"].isna().any():
    raise ValueError("Unknown event type detected.")


# ======================================
# 4. VALIDATE EVENT INDICES
# ======================================

if (
    (events["candle_index"] < 0) |
    (events["candle_index"] >= len(df) - 1)
).any():

    raise ValueError("Invalid event candle index.")

if not (
    events["earliest_execution_index"]
    == events["candle_index"] + 1
).all():

    raise ValueError("Invalid execution timing.")

# Confirm event timestamps match candle timestamps.

expected_times = df.loc[
    events["candle_index"].astype(int),
    "time"
].reset_index(drop=True)

actual_times = events["event_time"].reset_index(drop=True)

if not expected_times.equals(actual_times):
    raise ValueError("Event timestamps do not match candle data.")


# ======================================
# 5. CALCULATE EVENT OUTCOMES
# ======================================

results = []

for _, event in events.iterrows():

    direction = int(event["direction"])

    event_index = int(event["candle_index"])

    entry_index = int(
        event["earliest_execution_index"]
    )

    entry_price = float(
        df.loc[entry_index, "open"]
    )

    for horizon in HORIZONS:

        exit_index = entry_index + horizon - 1

        # Insufficient future data
        if exit_index >= len(df):
            continue

        future = df.loc[
            entry_index:exit_index
        ]

        exit_price = float(
            df.loc[exit_index, "close"]
        )

        # Direction-adjusted return in price units.
        directional_return = (
            (exit_price - entry_price) * direction
        )

        # Maximum favourable excursion.
        if direction == 1:

            mfe = (
                future["high"].max() - entry_price
            )

            mae = (
                entry_price - future["low"].min()
            )

        else:

            mfe = (
                entry_price - future["low"].min()
            )

            mae = (
                future["high"].max() - entry_price
            )

        results.append({

            "event_time": event["event_time"],

            "event_type": event["event_type"],

            "event_direction": direction,

            "horizon_bars": horizon,

            "entry_index": entry_index,

            "entry_price": entry_price,

            "exit_price": exit_price,

            "directional_return": directional_return,

            "mfe": mfe,

            "mae": mae,

            "profitable": directional_return > 0,

            "event_index": event_index

        })


# ======================================
# 6. CREATE RESULTS DATAFRAME
# ======================================

outcomes = pd.DataFrame(results)

if outcomes.empty:
    raise ValueError("No event outcomes calculated.")

print("\nOutcome calculations completed.")

print("Total observations:", len(outcomes))


# ======================================
# 7. OVERALL PERFORMANCE
# ======================================

print("\n======================================")
print("OVERALL EVENT PERFORMANCE")
print("======================================")

overall = outcomes.groupby(
    "horizon_bars"
).agg(

    observations=("profitable", "count"),

    win_rate=("profitable", "mean"),

    average_return=("directional_return", "mean"),

    median_return=("directional_return", "median"),

    average_mfe=("mfe", "mean"),

    average_mae=("mae", "mean")

)

overall["win_rate"] *= 100

print(overall.round(3))


# ======================================
# 8. PERFORMANCE BY EVENT TYPE
# ======================================

print("\n======================================")
print("PERFORMANCE BY EVENT TYPE")
print("======================================")

event_analysis = outcomes.groupby(
    ["event_type", "horizon_bars"]
).agg(

    observations=("profitable", "count"),

    win_rate=("profitable", "mean"),

    average_return=("directional_return", "mean"),

    median_return=("directional_return", "median"),

    average_mfe=("mfe", "mean"),

    average_mae=("mae", "mean")

)

event_analysis["win_rate"] *= 100

print(event_analysis.round(3))


# ======================================
# 9. PERFORMANCE BY DIRECTION
# ======================================

print("\n======================================")
print("BULLISH VS BEARISH PERFORMANCE")
print("======================================")

direction_analysis = outcomes.groupby(
    ["event_direction", "horizon_bars"]
).agg(

    observations=("profitable", "count"),

    win_rate=("profitable", "mean"),

    average_return=("directional_return", "mean"),

    average_mfe=("mfe", "mean"),

    average_mae=("mae", "mean")

)

direction_analysis["win_rate"] *= 100

print(direction_analysis.round(3))


# ======================================
# 10. PERFORMANCE BY BOS / CHOCH
# ======================================

outcomes["event_category"] = outcomes[
    "event_type"
].apply(

    lambda x: "BOS" if "BOS" in x else "CHOCH"

)

print("\n======================================")
print("BOS VS CHOCH PERFORMANCE")
print("======================================")

category_analysis = outcomes.groupby(
    ["event_category", "horizon_bars"]
).agg(

    observations=("profitable", "count"),

    win_rate=("profitable", "mean"),

    average_return=("directional_return", "mean"),

    average_mfe=("mfe", "mean"),

    average_mae=("mae", "mean")

)

category_analysis["win_rate"] *= 100

print(category_analysis.round(3))


# ======================================
# 11. EXPORT RESULTS
# ======================================

OUTPUT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

outcomes.to_csv(

    OUTPUT_DIRECTORY /
    "structure_event_outcomes.csv",

    index=False

)

overall.to_csv(

    OUTPUT_DIRECTORY /
    "structure_overall_performance.csv"

)

event_analysis.to_csv(

    OUTPUT_DIRECTORY /
    "structure_performance_by_event.csv"

)

print("\n======================================")
print("ANALYSIS COMPLETED")
print("======================================")

print("Individual outcomes saved.")

print("Overall summary saved.")

print("Event comparison saved.")