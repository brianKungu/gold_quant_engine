import pandas as pd
import numpy as np
from pathlib import Path

# ==========================================================
# CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CANDLE_FILE = PROJECT_ROOT / "data" / "raw" / "XAUUSD_M15.csv"
EVENT_FILE = PROJECT_ROOT / "backtests" / "historical_structure_events.csv"

OUTPUT_DIR = PROJECT_ROOT / "backtests"

HORIZON_BARS = 32
RANDOM_TRIALS = 500
BOOTSTRAP_TRIALS = 1000
RANDOM_SEED = 42


# ==========================================================
# LOAD DATA
# ==========================================================

print("\nLoading datasets...")

candles = pd.read_csv(CANDLE_FILE, parse_dates=["time"])
events = pd.read_csv(EVENT_FILE, parse_dates=["event_time"])

candles = candles.sort_values("time").reset_index(drop=True)
events = events.sort_values("candle_index").reset_index(drop=True)

required_candle_columns = ["time", "open", "high", "low", "close"]
required_event_columns = ["event_time", "candle_index", "event_type"]

for column in required_candle_columns:
    if column not in candles.columns:
        raise ValueError(f"Missing candle column: {column}")

for column in required_event_columns:
    if column not in events.columns:
        raise ValueError(f"Missing event column: {column}")

if candles["time"].duplicated().any():
    raise ValueError("Duplicate candle timestamps detected.")

if events["candle_index"].duplicated().any():
    raise ValueError("Duplicate event candle indices detected.")

if not candles["time"].is_monotonic_increasing:
    raise ValueError("Candles are not chronological.")

print(f"Candles loaded: {len(candles):,}")
print(f"Events loaded: {len(events):,}")


# ==========================================================
# PREPARE EVENT OUTCOMES
# ==========================================================

print("\nPreparing event outcomes...")

direction_map = {
    "BULLISH_BOS": 1,
    "BULLISH_CHOCH": 1,
    "BEARISH_BOS": -1,
    "BEARISH_CHOCH": -1
}

events["direction"] = events["event_type"].map(direction_map)

if events["direction"].isna().any():
    raise ValueError("Unknown event type detected.")

outcomes = []

for _, event in events.iterrows():

    event_index = int(event["candle_index"])

    # Entry is the candle after the event candle.
    entry_index = event_index + 1

    # Exit after the specified holding period.
    exit_index = entry_index + HORIZON_BARS - 1

    if entry_index < 0 or exit_index >= len(candles):
        continue

    entry_price = float(candles.loc[entry_index, "open"])
    exit_price = float(candles.loc[exit_index, "close"])

    directional_return = (
        (exit_price - entry_price) * event["direction"]
    )

    outcomes.append({
        "event_time": event["event_time"],
        "event_type": event["event_type"],
        "direction": int(event["direction"]),
        "event_index": event_index,
        "entry_index": entry_index,
        "exit_index": exit_index,
        "year": candles.loc[entry_index, "time"].year,
        "directional_return": directional_return
    })

event_outcomes = pd.DataFrame(outcomes)

if event_outcomes.empty:
    raise ValueError("No valid event outcomes.")

print(f"Valid event outcomes: {len(event_outcomes):,}")


# ==========================================================
# REMOVE OVERLAPPING EVENT WINDOWS
# ==========================================================

print("\nRemoving overlapping event windows...")

event_outcomes = event_outcomes.sort_values(
    "entry_index"
).reset_index(drop=True)

selected_events = []
last_exit_index = -1

for _, row in event_outcomes.iterrows():

    if row["entry_index"] > last_exit_index:

        selected_events.append(row)

        last_exit_index = int(row["exit_index"])

signals = pd.DataFrame(selected_events).reset_index(drop=True)

print(f"Original valid events: {len(event_outcomes):,}")
print(f"Non-overlapping events: {len(signals):,}")
print(
    f"Events removed: "
    f"{len(event_outcomes) - len(signals):,}"
)

if signals.empty:
    raise ValueError("No non-overlapping events remain.")


# ==========================================================
# SIGNAL PERFORMANCE
# ==========================================================

def calculate_metrics(data):

    returns = data["directional_return"]

    return {
        "observations": len(data),
        "win_rate_pct": (returns > 0).mean() * 100,
        "average_return": returns.mean(),
        "median_return": returns.median(),
        "average_winning_return": (
            returns[returns > 0].mean()
            if (returns > 0).any() else np.nan
        ),
        "average_losing_return": (
            returns[returns < 0].mean()
            if (returns < 0).any() else np.nan
        )
    }


signal_metrics = calculate_metrics(signals)

print("\n========== SIGNAL PERFORMANCE ==========")

for key, value in signal_metrics.items():
    print(f"{key}: {value}")


# ==========================================================
# PERFORMANCE BY EVENT TYPE
# ==========================================================

print("\n========== PERFORMANCE BY EVENT TYPE ==========")

event_type_results = []

for event_type, group in signals.groupby("event_type"):

    metrics = calculate_metrics(group)

    metrics["event_type"] = event_type

    event_type_results.append(metrics)

event_type_results = pd.DataFrame(event_type_results)

print(event_type_results.to_string(index=False))


# ==========================================================
# RANDOM ENTRY BENCHMARK
# Match each signal's year and direction.
# Random windows must also be non-overlapping.
# ==========================================================

print("\n========== RANDOM ENTRY BENCHMARK ==========")

rng = np.random.default_rng(RANDOM_SEED)

number_of_candles = len(candles)

eligible_starts = np.arange(
    0,
    number_of_candles - HORIZON_BARS + 1
)

candidate_years = candles.loc[
    eligible_starts, "time"
].dt.year.to_numpy()

# Precalculate random-entry outcomes for both directions.
random_returns = {}

for direction in [1, -1]:

    returns = []

    for start in eligible_starts:

        exit_index = start + HORIZON_BARS - 1

        entry_price = float(candles.loc[start, "open"])
        exit_price = float(candles.loc[exit_index, "close"])

        returns.append(
            (exit_price - entry_price) * direction
        )

    random_returns[direction] = np.array(returns)


# Required number of random entries per year and direction.
strata = (
    signals.groupby(["year", "direction"])
    .size()
    .to_dict()
)

# Candidate starts for each matching year and direction.
candidate_groups = {}

for (year, direction), required_count in strata.items():

    positions = np.where(candidate_years == year)[0]

    candidate_groups[(year, direction)] = (
        eligible_starts[positions]
    )


def generate_random_trial():

    occupied = np.zeros(number_of_candles, dtype=bool)

    selected_returns = []

    # Process smaller groups first.
    ordered_strata = sorted(
        strata.items(),
        key=lambda item: len(
            candidate_groups[item[0]]
        )
    )

    for (year, direction), required_count in ordered_strata:

        candidates = candidate_groups[(year, direction)].copy()

        rng.shuffle(candidates)

        selected_count = 0

        for start in candidates:

            end = start + HORIZON_BARS - 1

            # Prevent overlapping random windows.
            if occupied[start:end + 1].any():
                continue

            occupied[start:end + 1] = True

            return_value = (
                random_returns[direction][start]
            )

            selected_returns.append(return_value)

            selected_count += 1

            if selected_count == required_count:
                break

        if selected_count < required_count:
            return None

    return np.array(selected_returns)


random_means = []
random_win_rates = []

for trial in range(RANDOM_TRIALS):

    random_result = generate_random_trial()

    if random_result is None:
        continue

    random_means.append(random_result.mean())

    random_win_rates.append(
        (random_result > 0).mean() * 100
    )

if len(random_means) < 100:
    raise RuntimeError(
        "Too few successful random trials. "
        "Reduce the number of trials or investigate "
        "the sampling constraints."
    )

random_means = np.array(random_means)
random_win_rates = np.array(random_win_rates)

print(f"Successful random trials: {len(random_means)}")

print(
    "Random average return:",
    round(random_means.mean(), 4)
)

print(
    "Random average win rate:",
    round(random_win_rates.mean(), 2),
    "%"
)

print(
    "Random mean-return 95% range:",
    np.percentile(random_means, [2.5, 97.5])
)

# One-sided empirical comparison:
# How often did random entries achieve a mean return
# at least as high as our structural signals?

empirical_p = (
    1 + np.sum(random_means >= signal_metrics["average_return"])
) / (
    len(random_means) + 1
)

print(
    "Empirical p-value (random mean >= signal mean):",
    round(empirical_p, 4)
)


# ==========================================================
# WEEKLY BLOCK BOOTSTRAP
# Preserves clustering of events within each calendar week.
# ==========================================================

print("\n========== WEEKLY BLOCK BOOTSTRAP ==========")

signals["week"] = (
    pd.to_datetime(signals["event_time"])
    .dt.to_period("W")
    .astype(str)
)

weekly_groups = [
    group["directional_return"].to_numpy()
    for _, group in signals.groupby("week")
]

bootstrap_means = []

for _ in range(BOOTSTRAP_TRIALS):

    sampled_week_indices = rng.integers(
        0,
        len(weekly_groups),
        size=len(weekly_groups)
    )

    sampled_returns = np.concatenate([
        weekly_groups[index]
        for index in sampled_week_indices
    ])

    bootstrap_means.append(sampled_returns.mean())

confidence_interval = np.percentile(
    bootstrap_means,
    [2.5, 97.5]
)

print(
    "Signal average return:",
    round(signal_metrics["average_return"], 4)
)

print(
    "Weekly block-bootstrap 95% confidence interval:",
    confidence_interval
)


# ==========================================================
# SAVE RESULTS
# ==========================================================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

signals.to_csv(
    OUTPUT_DIR / "robustness_non_overlapping_signals.csv",
    index=False
)

event_type_results.to_csv(
    OUTPUT_DIR / "robustness_by_event_type.csv",
    index=False
)

summary = pd.DataFrame([
    {
        "test": "Structural signals",
        "observations": len(signals),
        "average_return": signal_metrics["average_return"],
        "win_rate_pct": signal_metrics["win_rate_pct"]
    },
    {
        "test": "Random benchmark average",
        "observations": len(signals),
        "average_return": random_means.mean(),
        "win_rate_pct": random_win_rates.mean()
    }
])

summary.to_csv(
    OUTPUT_DIR / "robustness_summary.csv",
    index=False
)

random_distribution = pd.DataFrame({
    "random_mean_return": random_means,
    "random_win_rate_pct": random_win_rates
})

random_distribution.to_csv(
    OUTPUT_DIR / "robustness_random_trials.csv",
    index=False
)

print("\nResults saved in the backtests folder.")

print("\n========== ROBUSTNESS TEST COMPLETE ==========")
