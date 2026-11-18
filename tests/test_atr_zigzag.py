import pandas as pd

from strategies.market_structure import detect_atr_zigzag


# ======================================
# 1. LOAD DATA
# ======================================

df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv",
    parse_dates=["time"]
)

df = df.reset_index(drop=True)

print("\nDataset loaded successfully.")
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

df["atr"] = df["true_range"].rolling(14).mean()


# ======================================
# 3. TEST DIFFERENT ATR MULTIPLIERS
# ======================================

multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]

results = []

print("\n======================================")
print("ATR ZIGZAG COMPARISON")
print("======================================")

for multiplier in multipliers:

    pivots = detect_atr_zigzag(
        df,
        atr_column="atr",
        multiplier=multiplier
    )

    if len(pivots) < 2:
        print(f"\n{multiplier} ATR: Insufficient pivots.")
        continue

    # Calculate distance between consecutive pivots

    pivots["leg_distance"] = (
        pivots["pivot_price"].diff().abs()
    )

    # Candles between consecutive pivots

    pivots["bars_between_pivots"] = (
        pivots["pivot_index"].diff()
    )

    # Pivot confirmation delay

    pivots["confirmation_delay"] = (
        pivots["confirmation_index"] -
        pivots["pivot_index"]
    )

    highs = (pivots["pivot_type"] == "HIGH").sum()
    lows = (pivots["pivot_type"] == "LOW").sum()

    # Check alternation

    consecutive_types = (
        pivots["pivot_type"] ==
        pivots["pivot_type"].shift(1)
    ).sum()

    results.append({
        "Multiplier": multiplier,
        "Total Pivots": len(pivots),
        "Highs": highs,
        "Lows": lows,
        "Median Leg": pivots["leg_distance"].median(),
        "Average Leg": pivots["leg_distance"].mean(),
        "Median Bars": pivots["bars_between_pivots"].median(),
        "Average Bars": pivots["bars_between_pivots"].mean(),
        "Median Confirmation Delay": pivots["confirmation_delay"].median(),
        "Consecutive Types": consecutive_types
    })

    print(f"\n========== {multiplier} ATR ==========")

    print("Total pivots:", len(pivots))
    print("Swing highs:", highs)
    print("Swing lows:", lows)

    print(
        "Median leg distance:",
        round(pivots["leg_distance"].median(), 2)
    )

    print(
        "Average leg distance:",
        round(pivots["leg_distance"].mean(), 2)
    )

    print(
        "Median bars between pivots:",
        pivots["bars_between_pivots"].median()
    )

    print(
        "Average bars between pivots:",
        round(pivots["bars_between_pivots"].mean(), 2)
    )

    print(
        "Median confirmation delay:",
        pivots["confirmation_delay"].median()
    )

    print(
        "Consecutive pivot types:",
        consecutive_types
    )

    # Latest 10 pivots

    print("\nLatest 10 pivots:")

    print(
        pivots[
            [
                "pivot_time",
                "confirmation_time",
                "pivot_type",
                "pivot_price",
                "leg_distance",
                "confirmation_delay"
            ]
        ].tail(10).to_string(index=False)
    )


# ======================================
# 4. SUMMARY COMPARISON
# ======================================

print("\n======================================")
print("FINAL MULTIPLIER COMPARISON")
print("======================================")

summary = pd.DataFrame(results)

print(summary.to_string(index=False))


# ======================================
# 5. FINAL VALIDATION
# ======================================

print("\n======================================")
print("VALIDATION")
print("======================================")

for multiplier in multipliers:

    pivots = detect_atr_zigzag(
        df,
        multiplier=multiplier
    )

    if len(pivots) == 0:
        print(f"{multiplier} ATR: No pivots detected.")
        continue

    consecutive_types = (
        pivots["pivot_type"] ==
        pivots["pivot_type"].shift(1)
    ).sum()

    duplicate_times = pivots["confirmation_time"].duplicated().sum()

    invalid_delays = (
        pivots["confirmation_index"] <
        pivots["pivot_index"]
    ).sum()

    print(f"\n{multiplier} ATR:")

    print("Alternation violations:", consecutive_types)
    print("Duplicate confirmation times:", duplicate_times)
    print("Invalid confirmation delays:", invalid_delays)

print("\nATR ZIGZAG TEST COMPLETED.")