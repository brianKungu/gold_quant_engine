import pandas as pd
import numpy as np

# =====================================================
# CONFIGURATION
# =====================================================

DATA_FILE = "data/raw/XAUUSD_M15.csv"
SIGNALS_FILE = "backtests/robustness_non_overlapping_signals.csv"

HORIZON = 32
RANDOM_TRIALS = 500
RANDOM_SEED = 42

PERIODS = {
    "DEVELOPMENT_2022_2024": (2022, 2024),
    "VALIDATION_2025": (2025, 2025),
    "RECENT_TEST_2026": (2026, 2026),
}

rng = np.random.default_rng(RANDOM_SEED)


# =====================================================
# LOAD AND VALIDATE DATA
# =====================================================

candles = pd.read_csv(DATA_FILE)
signals = pd.read_csv(SIGNALS_FILE)

candles["time"] = pd.to_datetime(candles["time"])
signals["event_time"] = pd.to_datetime(signals["event_time"])

candles = candles.sort_values("time").reset_index(drop=True)

required_candle_columns = ["time", "open", "close"]
required_signal_columns = [
    "event_time",
    "event_type",
    "direction",
    "event_index",
    "entry_index",
    "exit_index",
    "year",
    "directional_return",
]

for column in required_candle_columns:
    if column not in candles.columns:
        raise ValueError(f"Missing candle column: {column}")

for column in required_signal_columns:
    if column not in signals.columns:
        raise ValueError(f"Missing signal column: {column}")

if candles["time"].duplicated().any():
    raise ValueError("Duplicate candle timestamps.")

if not candles["time"].is_monotonic_increasing:
    raise ValueError("Candles are not chronological.")

if not signals["direction"].isin([-1, 1]).all():
    raise ValueError("Invalid signal direction.")

# Convert indices to integers.
for column in ["event_index", "entry_index", "exit_index"]:
    signals[column] = signals[column].astype(int)

# Verify indices are within the original dataset.
if (
    (signals["event_index"] < 0)
    | (signals["exit_index"] >= len(candles))
).any():
    raise ValueError("Signal indices exceed candle dataset.")

# Verify event timestamps match original candle indices.
expected_event_times = candles.loc[
    signals["event_index"], "time"
].reset_index(drop=True)

actual_event_times = signals["event_time"].reset_index(drop=True)

if not expected_event_times.equals(actual_event_times):
    raise ValueError(
        "Event timestamps do not match original candle indices."
    )

# Verify entry and exit timing.
if not (
    signals["entry_index"] == signals["event_index"] + 1
).all():
    raise ValueError("Unexpected entry index.")

if not (
    signals["exit_index"] - signals["entry_index"] == HORIZON - 1
).all():
    raise ValueError("Unexpected holding period.")

# Recalculate returns to verify stored values.
calculated_returns = (
    candles.loc[signals["exit_index"], "close"].to_numpy()
    - candles.loc[signals["entry_index"], "open"].to_numpy()
) * signals["direction"].to_numpy()

if not np.allclose(
    calculated_returns,
    signals["directional_return"].to_numpy(),
    atol=1e-6
):
    raise ValueError("Stored returns do not match candle data.")

print("\nDATA VALIDATION PASSED")
print("-" * 55)
print(f"Candles: {len(candles):,}")
print(f"Signals: {len(signals):,}")
print(f"First candle: {candles['time'].min()}")
print(f"Last candle: {candles['time'].max()}")


# =====================================================
# METRICS
# =====================================================

def calculate_metrics(data):

    returns = data["directional_return"]

    if len(returns) == 0:
        return {
            "observations": 0,
            "win_rate_pct": np.nan,
            "average_return": np.nan,
            "median_return": np.nan,
        }

    return {
        "observations": len(returns),
        "win_rate_pct": (returns > 0).mean() * 100,
        "average_return": returns.mean(),
        "median_return": returns.median(),
    }


# =====================================================
# PREPARE RANDOM BENCHMARK
# =====================================================

# All actual signal windows are excluded from random controls.
excluded_indices = set()

for _, row in signals.iterrows():

    excluded_indices.update(
        range(
            row["entry_index"],
            row["exit_index"] + 1
        )
    )


# =====================================================
# PREPARE RANDOM BENCHMARK
# =====================================================

def generate_random_controls(period_signals):

    requirements = (
        period_signals
        .groupby(["year", "direction"])
        .size()
        .to_dict()
    )

    occupied = set()
    random_returns = []

    groups = list(requirements.keys())
    rng.shuffle(groups)

    for year, direction in groups:

        required_count = requirements[(year, direction)]

        year_indices = np.flatnonzero(
            candles["time"].dt.year.to_numpy() == year
        )

        if len(year_indices) <= HORIZON:
            return None

        first_index = int(year_indices[0])
        last_index = int(year_indices[-1])

        candidates = np.arange(
            first_index,
            last_index - HORIZON + 2
        )

        rng.shuffle(candidates)

        accepted = 0

        for entry_index in candidates:

            exit_index = entry_index + HORIZON - 1

            window = set(
                range(entry_index, exit_index + 1)
            )

            # Random windows cannot overlap each other.
            if window.intersection(occupied):
                continue

            entry_price = float(
                candles.loc[entry_index, "open"]
            )

            exit_price = float(
                candles.loc[exit_index, "close"]
            )

            directional_return = (
                exit_price - entry_price
            ) * direction

            random_returns.append(directional_return)

            occupied.update(window)

            accepted += 1

            if accepted == required_count:
                break

        if accepted < required_count:
            return None

    return np.array(random_returns)

# =====================================================
# RUN PERIOD ANALYSIS
# =====================================================

period_results = []
event_results = []
random_results = []

for period_name, (start_year, end_year) in PERIODS.items():

    print("\n")
    print("=" * 65)
    print(f"ANALYSING {period_name}")
    print("=" * 65)

    period_signals = signals[
        signals["year"].between(start_year, end_year)
    ].copy()

    if period_signals.empty:
        print("No signals found.")
        continue

    # -----------------------------
    # Overall signal performance
    # -----------------------------

    metrics = calculate_metrics(period_signals)

    period_results.append({
        "period": period_name,
        **metrics
    })

    print("\nOVERALL PERFORMANCE")
    print(pd.DataFrame([metrics]).to_string(index=False))

    # -----------------------------
    # Performance by event type
    # -----------------------------

    breakdown_rows = []

    for event_type, group in period_signals.groupby("event_type"):

        breakdown_rows.append({
            "period": period_name,
            "event_type": event_type,
            **calculate_metrics(group)
        })

    breakdown = pd.DataFrame(breakdown_rows)

    event_results.append(breakdown)

    print("\nPERFORMANCE BY EVENT TYPE")
    print(breakdown.to_string(index=False))

    # -----------------------------
    # Random benchmark
    # -----------------------------

    signal_mean = period_signals[
        "directional_return"
    ].mean()

    trial_means = []

    for trial in range(RANDOM_TRIALS):

        controls = generate_random_controls(period_signals)

        if controls is not None:
            trial_means.append(controls.mean())

    if len(trial_means) == 0:

        print("\nWARNING: No valid random benchmark trials.")
        continue

    random_means = np.array(trial_means)

    p_value = (
        1 + np.sum(random_means >= signal_mean)
    ) / (
        1 + len(random_means)
    )

    random_summary = {
        "period": period_name,
        "signal_mean": signal_mean,
        "random_mean": random_means.mean(),
        "difference": signal_mean - random_means.mean(),
        "empirical_p_value": p_value,
        "successful_trials": len(random_means),
    }

    random_results.append(random_summary)

    print("\nRANDOM BENCHMARK")
    print(pd.DataFrame([random_summary]).to_string(index=False))


# =====================================================
# SAVE RESULTS
# =====================================================

pd.DataFrame(period_results).to_csv(
    "backtests/time_period_summary.csv",
    index=False
)

if event_results:
    pd.concat(event_results, ignore_index=True).to_csv(
        "backtests/time_period_event_breakdown.csv",
        index=False
    )

pd.DataFrame(random_results).to_csv(
    "backtests/time_period_random_benchmark.csv",
    index=False
)


# =====================================================
# FINAL OUTPUT
# =====================================================

print("\n")
print("=" * 65)
print("TIME-BASED VALIDATION COMPLETE")
print("=" * 65)

print("\nOVERALL PERIOD COMPARISON")

print(
    pd.DataFrame(period_results).to_string(index=False)
)

print("\nRANDOM BENCHMARK COMPARISON")

if random_results:
    print(
        pd.DataFrame(random_results).to_string(index=False)
    )

print("\nFILES SAVED:")
print("1. backtests/time_period_summary.csv")
print("2. backtests/time_period_event_breakdown.csv")
print("3. backtests/time_period_random_benchmark.csv")