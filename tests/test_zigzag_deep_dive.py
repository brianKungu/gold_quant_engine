
import pandas as pd

from strategies.market_structure import detect_atr_zigzag


# ======================================
# 1. LOAD HISTORICAL DATA
# ======================================

df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv",
    parse_dates=["time"]
)

df = df.reset_index(drop=True)

if df["time"].duplicated().any():
    raise ValueError("Duplicate timestamps detected.")

if not df["time"].is_monotonic_increasing:
    raise ValueError("Data is not chronological.")

print("Dataset loaded:", len(df), "candles")


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
# 3. DEFINE VOLATILITY REGIMES
# ======================================

valid_atr = df["atr"].dropna()

low_threshold = valid_atr.quantile(0.33)
high_threshold = valid_atr.quantile(0.66)

df["volatility_regime"] = "MEDIUM"

df.loc[
    df["atr"] <= low_threshold,
    "volatility_regime"
] = "LOW"

df.loc[
    df["atr"] > high_threshold,
    "volatility_regime"
] = "HIGH"

print("\nVolatility thresholds:")
print("Low:", round(low_threshold, 4))
print("High:", round(high_threshold, 4))


# ======================================
# 4. TEST ATR MULTIPLIERS
# ======================================

multipliers = [2.0, 2.5]

for multiplier in multipliers:

    print("\n")
    print("=" * 60)
    print(f"ATR ZIGZAG DEEP DIVE: {multiplier} ATR")
    print("=" * 60)

    pivots = detect_atr_zigzag(
        df,
        atr_column="atr",
        multiplier=multiplier
    )

    if len(pivots) < 2:
        print("Insufficient pivots.")
        continue

    # ----------------------------------
    # A. CALCULATE PIVOT METRICS
    # ----------------------------------

    pivots["confirmation_delay"] = (
        pivots["confirmation_index"] -
        pivots["pivot_index"]
    )

    pivots["year"] = pd.to_datetime(
        pivots["pivot_time"]
    ).dt.year

    pivots["confirmation_year"] = pd.to_datetime(
        pivots["confirmation_time"]
    ).dt.year

    pivots["leg_distance"] = (
        pivots["pivot_price"].diff().abs()
    )

    # ----------------------------------
    # B. GENERAL STATISTICS
    # ----------------------------------

    print("\nGENERAL STATISTICS")

    print("Total pivots:", len(pivots))

    print(
        "High pivots:",
        (pivots["pivot_type"] == "HIGH").sum()
    )

    print(
        "Low pivots:",
        (pivots["pivot_type"] == "LOW").sum()
    )

    print(
        "Median confirmation delay:",
        pivots["confirmation_delay"].median()
    )

    print(
        "Average confirmation delay:",
        round(
            pivots["confirmation_delay"].mean(),
            2
        )
    )

    print(
        "Median leg distance:",
        round(
            pivots["leg_distance"].median(),
            2
        )
    )

    print(
        "Average leg distance:",
        round(
            pivots["leg_distance"].mean(),
            2
        )
    )

    # ----------------------------------
    # C. CONFIRMATION SPEED
    # ----------------------------------

    print("\nCONFIRMATION SPEED")

    total = len(pivots)

    for bars in [1, 2, 4, 8, 12]:

        count = (
            pivots["confirmation_delay"] <= bars
        ).sum()

        percentage = (count / total) * 100

        print(
            f"Within {bars} candles: "
            f"{count} ({percentage:.2f}%)"
        )

    # ----------------------------------
    # D. CONFIRMATION DELAY DISTRIBUTION
    # ----------------------------------

    print("\nDELAY DISTRIBUTION")

    print(
        pivots["confirmation_delay"]
        .describe()
        .round(2)
    )

    # ----------------------------------
    # E. YEARLY ANALYSIS
    # ----------------------------------

    print("\nYEARLY PIVOT DISTRIBUTION")

    yearly = pivots.groupby("year").agg(
        total_pivots=("pivot_type", "count"),
        median_leg_distance=("leg_distance", "median"),
        average_leg_distance=("leg_distance", "mean"),
        median_confirmation_delay=(
            "confirmation_delay", "median"
        )
    )

    print(yearly.round(2).to_string())

    # ----------------------------------
    # F. VOLATILITY REGIME ANALYSIS
    # ----------------------------------

    print("\nVOLATILITY REGIME ANALYSIS")

    # Match each pivot to the volatility regime
    # at the candle where it was confirmed.

    regime_lookup = df[
        ["time", "volatility_regime"]
    ].rename(
        columns={"time": "confirmation_time"}
    )

    pivots = pivots.merge(
        regime_lookup,
        on="confirmation_time",
        how="left",
        validate="many_to_one"
    )

    regime_stats = pivots.groupby(
        "volatility_regime",
        observed=True
    ).agg(
        total_pivots=("pivot_type", "count"),
        median_leg_distance=("leg_distance", "median"),
        average_leg_distance=("leg_distance", "mean"),
        median_confirmation_delay=(
            "confirmation_delay", "median"
        )
    )

    print(regime_stats.round(2).to_string())

    # ----------------------------------
    # G. STRUCTURAL VALIDATION
    # ----------------------------------

    print("\nVALIDATION")

    alternation_violations = (
        pivots["pivot_type"]
        .eq(pivots["pivot_type"].shift())
        .sum()
    )

    duplicate_confirmations = (
        pivots["confirmation_time"].duplicated().sum()
    )

    invalid_delays = (
        pivots["confirmation_delay"] < 0
    ).sum()

    missing_regimes = (
        pivots["volatility_regime"].isna().sum()
    )

    print(
        "Alternation violations:",
        alternation_violations
    )

    print(
        "Duplicate confirmation times:",
        duplicate_confirmations
    )

    print(
        "Invalid confirmation delays:",
        invalid_delays
    )

    print(
        "Missing volatility regimes:",
        missing_regimes
    )

    # ----------------------------------
    # H. LATEST 10 PIVOTS
    # ----------------------------------

    print("\nLATEST 10 PIVOTS")

    print(
        pivots[
            [
                "pivot_time",
                "confirmation_time",
                "pivot_type",
                "pivot_price",
                "leg_distance",
                "confirmation_delay",
                "volatility_regime"
            ]
        ].tail(10).to_string(index=False)
    )


print("\nDEEP-DIVE ANALYSIS COMPLETED.")
