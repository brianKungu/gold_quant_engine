import pandas as pd
import numpy as np

# =====================================================
# CONFIGURATION
# =====================================================

DATA_FILE = "data/raw/XAUUSD_M15.csv"

SIGNALS_FILE = (
    "backtests/robustness_non_overlapping_signals.csv"
)

HORIZON = 32
RANDOM_TRIALS = 500
RANDOM_SEED = 42

PERIODS = {
    "2022_2024": (2022, 2024),
    "2025": (2025, 2025),
    "2026": (2026, 2026),
}

rng = np.random.default_rng(RANDOM_SEED)


# =====================================================
# LOAD DATA
# =====================================================

candles = pd.read_csv(DATA_FILE)
signals = pd.read_csv(SIGNALS_FILE)

candles["time"] = pd.to_datetime(candles["time"])
signals["event_time"] = pd.to_datetime(signals["event_time"])

candles = candles.sort_values("time").reset_index(drop=True)

required_columns = [
    "event_time",
    "event_type",
    "direction",
    "event_index",
    "entry_index",
    "exit_index",
    "year",
    "directional_return",
]

for column in required_columns:
    if column not in signals.columns:
        raise ValueError(f"Missing signal column: {column}")

if candles["time"].duplicated().any():
    raise ValueError("Duplicate candle timestamps.")

for column in ["event_index", "entry_index", "exit_index"]:
    signals[column] = signals[column].astype(int)

if not signals["direction"].isin([-1, 1]).all():
    raise ValueError("Invalid signal direction.")

# Verify original candle indices.
expected_times = candles.loc[
    signals["event_index"], "time"
].reset_index(drop=True)

actual_times = signals["event_time"].reset_index(drop=True)

if not expected_times.equals(actual_times):
    raise ValueError("Event timestamps do not match candle indices.")

# Verify holding period.
if not (
    signals["exit_index"] - signals["entry_index"]
    == HORIZON - 1
).all():
    raise ValueError("Unexpected holding period.")

# Recalculate returns.
calculated_returns = (
    candles.loc[signals["exit_index"], "close"].to_numpy()
    - candles.loc[signals["entry_index"], "open"].to_numpy()
) * signals["direction"].to_numpy()

if not np.allclose(
    calculated_returns,
    signals["directional_return"].to_numpy(),
    atol=1e-6
):
    raise ValueError("Return validation failed.")

print("\nDATA VALIDATION PASSED")
print("-" * 55)
print(f"Candles: {len(candles):,}")
print(f"Signals: {len(signals):,}")


# =====================================================
# PERFORMANCE METRICS
# =====================================================

def calculate_metrics(returns):

    returns = np.asarray(returns, dtype=float)

    return {
        "observations": len(returns),
        "win_rate_pct": np.mean(returns > 0) * 100,
        "average_return": np.mean(returns),
        "median_return": np.median(returns),
        "percentile_25": np.percentile(returns, 25),
        "percentile_75": np.percentile(returns, 75),
        "best_return": np.max(returns),
        "worst_return": np.min(returns),
    }


# =====================================================
# RANDOM BENCHMARK
# =====================================================

def generate_random_controls(group):

    requirements = (
        group.groupby(["year", "direction"])
        .size()
        .to_dict()
    )

    occupied = np.zeros(len(candles), dtype=bool)

    random_returns = []

    groups = list(requirements.keys())
    rng.shuffle(groups)

    years = candles["time"].dt.year.to_numpy()

    for year, direction in groups:

        required_count = requirements[(year, direction)]

        year_indices = np.flatnonzero(years == year)

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

            # Random controls cannot overlap each other.
            if occupied[entry_index:exit_index + 1].any():
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

            occupied[entry_index:exit_index + 1] = True

            accepted += 1

            if accepted == required_count:
                break

        if accepted < required_count:
            return None

    return np.array(random_returns)


# =====================================================
# EVENT TYPE ANALYSIS
# =====================================================

results = []

random_distribution_results = []

for period_name, (start_year, end_year) in PERIODS.items():

    print("\n")
    print("=" * 75)
    print(f"PERIOD: {period_name}")
    print("=" * 75)

    period_signals = signals[
        signals["year"].between(start_year, end_year)
    ].copy()

    for event_type in sorted(period_signals["event_type"].unique()):

        group = period_signals[
            period_signals["event_type"] == event_type
        ].copy()

        signal_returns = group["directional_return"].to_numpy()

        signal_metrics = calculate_metrics(signal_returns)

        print("\n")
        print("-" * 65)
        print(f"EVENT TYPE: {event_type}")
        print("-" * 65)

        print(pd.DataFrame([signal_metrics]).to_string(index=False))

        # ---------------------------------------------
        # RANDOM BENCHMARK
        # ---------------------------------------------

        trial_means = []

        for trial in range(RANDOM_TRIALS):

            controls = generate_random_controls(group)

            if controls is not None:
                trial_means.append(controls.mean())

        if len(trial_means) == 0:

            print("WARNING: No valid random trials.")

            continue

        random_means = np.array(trial_means)

        signal_mean = signal_returns.mean()

        random_mean = random_means.mean()

        difference = signal_mean - random_mean

        p_value = (
            1 + np.sum(random_means >= signal_mean)
        ) / (
            1 + len(random_means)
        )

        result = {
            "period": period_name,
            "event_type": event_type,
            **signal_metrics,
            "random_mean": random_mean,
            "difference": difference,
            "random_2_5_percentile": np.percentile(
                random_means, 2.5
            ),
            "random_97_5_percentile": np.percentile(
                random_means, 97.5
            ),
            "empirical_p_value": p_value,
            "successful_trials": len(random_means),
        }

        results.append(result)

        random_distribution_results.extend([
            {
                "period": period_name,
                "event_type": event_type,
                "trial": index + 1,
                "random_mean": value,
            }
            for index, value in enumerate(random_means)
        ])

        print("\nRANDOM BENCHMARK")

        print(
            pd.DataFrame([{
                "signal_mean": signal_mean,
                "random_mean": random_mean,
                "difference": difference,
                "empirical_p_value": p_value,
                "successful_trials": len(random_means),
            }]).to_string(index=False)
        )


# =====================================================
# SAVE RESULTS
# =====================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    "backtests/event_type_robustness.csv",
    index=False
)

pd.DataFrame(random_distribution_results).to_csv(
    "backtests/event_type_random_trials.csv",
    index=False
)

print("\n")
print("=" * 75)
print("EVENT TYPE ANALYSIS COMPLETE")
print("=" * 75)

if not results_df.empty:

    print("\nFINAL COMPARISON")

    columns = [
        "period",
        "event_type",
        "observations",
        "win_rate_pct",
        "average_return",
        "median_return",
        "random_mean",
        "difference",
        "empirical_p_value",
    ]

    print(
        results_df[columns].to_string(index=False)
    )

print("\nFILES SAVED:")
print("1. backtests/event_type_robustness.csv")
print("2. backtests/event_type_random_trials.csv")