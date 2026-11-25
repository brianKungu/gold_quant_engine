import pandas as pd
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================

DATA_FILE = "data/raw/XAUUSD_M15.csv"

SIGNALS_FILE = (
    "backtests/robustness_non_overlapping_signals.csv"
)

TOP_N = 20

# ==========================================
# LOAD DATA
# ==========================================

candles = pd.read_csv(DATA_FILE)
signals = pd.read_csv(SIGNALS_FILE)

candles["time"] = pd.to_datetime(candles["time"])

signals["event_time"] = pd.to_datetime(
    signals["event_time"]
)

candles = candles.sort_values("time").reset_index(drop=True)

# ==========================================
# VALIDATE RETURNS
# ==========================================

signals["entry_price"] = candles.loc[
    signals["entry_index"], "open"
].to_numpy()

signals["exit_price"] = candles.loc[
    signals["exit_index"], "close"
].to_numpy()

signals["recalculated_return"] = (
    signals["exit_price"] - signals["entry_price"]
) * signals["direction"]

difference = (
    signals["recalculated_return"]
    - signals["directional_return"]
).abs()

if difference.max() > 0.000001:
    raise ValueError("Return calculation mismatch.")

print("\nRETURN VALIDATION PASSED")

# ==========================================
# CALCULATE TRADE EXCURSIONS
# ==========================================

records = []

for _, signal in signals.iterrows():

    entry = int(signal["entry_index"])
    exit_ = int(signal["exit_index"])

    window = candles.iloc[entry:exit_ + 1]

    entry_price = float(candles.loc[entry, "open"])
    exit_price = float(candles.loc[exit_, "close"])

    direction = int(signal["direction"])

    if direction == 1:

        favorable_excursion = (
            float(window["high"].max()) - entry_price
        )

        adverse_excursion = (
            entry_price - float(window["low"].min())
        )

    else:

        favorable_excursion = (
            entry_price - float(window["low"].min())
        )

        adverse_excursion = (
            float(window["high"].max()) - entry_price
        )

    close_changes = window["close"].diff().abs()

    max_single_bar_change = close_changes.max()

    time_gaps = (
        window["time"].diff()
        .dt.total_seconds()
        / 60
    )

    elapsed_minutes = (
        candles.loc[exit_, "time"]
        - candles.loc[entry, "time"]
    ).total_seconds() / 60 + 15

    gap_count = (time_gaps > 15).sum()

    maximum_bar_range = (
        window["high"] - window["low"]
    ).max()

    maximum_open_gap = (
        window["open"] - window["close"].shift(1)
    ).abs().max()

    records.append({
        "elapsed_minutes": elapsed_minutes,

        "gap_count": gap_count,

        "maximum_bar_range": maximum_bar_range,

        "maximum_open_gap": maximum_open_gap,

        "event_time": signal["event_time"],

        "event_type": signal["event_type"],

        "year": signal["year"],

        "direction": direction,

        "entry_index": entry,

        "exit_index": exit_,

        "entry_time": candles.loc[entry, "time"],

        "exit_time": candles.loc[exit_, "time"],

        "entry_price": entry_price,

        "exit_price": exit_price,

        "directional_return": signal["directional_return"],

        "favorable_excursion": favorable_excursion,

        "adverse_excursion": adverse_excursion,

        "maximum_single_bar_change": max_single_bar_change,

        "maximum_time_gap_minutes": time_gaps.max(),

        "window_high": window["high"].max(),

        "window_low": window["low"].min(),

    })

audit = pd.DataFrame(records)

# ==========================================
# TOP WINNERS
# ==========================================

print("\n")
print("=" * 75)
print("TOP 20 WINNING TRADES")
print("=" * 75)

winners = audit.nlargest(
    TOP_N,
    "directional_return"
)

print(
    winners.to_string(index=False)
)

# ==========================================
# TOP LOSERS
# ==========================================

print("\n")
print("=" * 75)
print("TOP 20 LOSING TRADES")
print("=" * 75)

losers = audit.nsmallest(
    TOP_N,
    "directional_return"
)

print(
    losers.to_string(index=False)
)

# ==========================================
# DATA QUALITY SUMMARY
# ==========================================

print("\n")
print("=" * 75)
print("EXTREME TRADE SUMMARY")
print("=" * 75)

print("\nMaximum single-bar price movement:")

print(
    audit["maximum_single_bar_change"].describe()
)

print("\nMaximum time gaps inside trade windows:")

print(
    audit["maximum_time_gap_minutes"].describe()
)

# ==========================================
# HOLDING PERIOD ANALYSIS
# ==========================================

print("\n")
print("=" * 75)
print("HOLDING PERIOD ANALYSIS")
print("=" * 75)

print("\nActual holding duration:")

print(
    audit["elapsed_minutes"].describe()
)

print("\nTrades with missing candle intervals:")

print(
    (audit["gap_count"] > 0).sum()
)

print("\nTrades with gaps exceeding 1 hour:")

print(
    (audit["maximum_time_gap_minutes"] > 60).sum()
)

print("\nTrades with gaps exceeding 24 hours:")

print(
    (audit["maximum_time_gap_minutes"] > 1440).sum()
)

print("\nTrades with more than 8 hours elapsed:")

print(
    (audit["elapsed_minutes"] > 480).sum()
)

print("\nTrades by event type and gap occurrence:")

print(
    audit.groupby("event_type").agg(
        total_trades=("event_type", "count"),
        trades_with_gaps=("gap_count", lambda x: (x > 0).sum()),
        average_duration=("elapsed_minutes", "mean"),
        maximum_duration=("elapsed_minutes", "max"),
        average_return=("directional_return", "mean")
    ).to_string()
)

# ==========================================
# CONTINUOUS VS INTERRUPTED TRADES
# ==========================================

print("\n")
print("=" * 75)
print("CONTINUOUS VS INTERRUPTED TRADE ANALYSIS")
print("=" * 75)

audit["gap_category"] = np.where(
    audit["gap_count"] == 0,
    "CONTINUOUS",
    "INTERRUPTED"
)

# Overall comparison
comparison = audit.groupby("gap_category").agg(
    trades=("directional_return", "count"),
    win_rate=("directional_return",
              lambda x: (x > 0).mean() * 100),
    average_return=("directional_return", "mean"),
    median_return=("directional_return", "median"),
    average_duration=("elapsed_minutes", "mean"),
    worst_trade=("directional_return", "min"),
    best_trade=("directional_return", "max")
).reset_index()

print("\nOVERALL COMPARISON")
print(comparison.to_string(index=False))


# Event type comparison
print("\n\nPERFORMANCE BY EVENT TYPE")

event_comparison = audit.groupby(
    ["event_type", "gap_category"]
).agg(
    trades=("directional_return", "count"),
    win_rate=("directional_return",
              lambda x: (x > 0).mean() * 100),
    average_return=("directional_return", "mean"),
    median_return=("directional_return", "median")
).reset_index()

print(event_comparison.to_string(index=False))


# Year comparison
print("\n\nPERFORMANCE BY YEAR")

year_comparison = audit.groupby(
    ["year", "gap_category"]
).agg(
    trades=("directional_return", "count"),
    win_rate=("directional_return",
              lambda x: (x > 0).mean() * 100),
    average_return=("directional_return", "mean"),
    median_return=("directional_return", "median")
).reset_index()

print(year_comparison.to_string(index=False))


# Save results
comparison.to_csv(
    "backtests/continuous_vs_interrupted.csv",
    index=False
)

event_comparison.to_csv(
    "backtests/gap_performance_by_event.csv",
    index=False
)

year_comparison.to_csv(
    "backtests/gap_performance_by_year.csv",
    index=False
)

print("\nCOMPARISON FILES SAVED")

# ==========================================
# EXPORT
# ==========================================

audit.to_csv(
    "backtests/extreme_trade_audit.csv",
    index=False
)

winners.to_csv(
    "backtests/top_20_winners.csv",
    index=False
)

losers.to_csv(
    "backtests/top_20_losers.csv",
    index=False
)

print("\nAUDIT FILES SAVED:")
print("1. backtests/extreme_trade_audit.csv")
print("2. backtests/top_20_winners.csv")
print("3. backtests/top_20_losers.csv")