import pandas as pd

from strategies.market_structure import (
    detect_swings,
    build_alternating_pivots
)

# Load historical data
df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv",
    parse_dates=["time"]
)

# Detect raw swings
df = detect_swings(df, lookback=5)

# Build clean alternating pivots
pivots = build_alternating_pivots(
    df,
    lookback=5
)

print("\n======================================")
print("PIVOT CLEANING RESULTS")
print("======================================")

print("\nOriginal swing highs:", df["swing_high"].sum())
print("Original swing lows:", df["swing_low"].sum())

print("\nCleaned pivot count:", len(pivots))

print("\nPivot distribution:")
print(pivots["pivot_type"].value_counts())

# Check whether consecutive pivot types remain
same_type = (
    pivots["pivot_type"] ==
    pivots["pivot_type"].shift(1)
)

print("\nConsecutive pivot types:", same_type.sum())

# Display latest pivots
print("\nLast 20 cleaned pivots:")

print(
    pivots.tail(20).to_string(index=False)
)

# Validate alternating sequence
assert same_type.sum() == 0, (
    "ERROR: Consecutive pivot types still exist!"
)

assert len(pivots) > 0, (
    "ERROR: No pivots detected!"
)

# Validate confirmation timestamps
assert (
    pivots["confirmation_time"] >= pivots["pivot_time"]
).all()

print("\nSUCCESS: Pivot sequence is alternating.")
print("SUCCESS: Confirmation timestamps are valid.")
