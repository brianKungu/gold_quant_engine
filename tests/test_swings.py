import pandas as pd

from strategies.market_structure import detect_swings


# Load XAUUSD M15 historical data
df = pd.read_csv(
    "data/raw/XAUUSD_M15.csv"
)

# Detect swing highs and lows
df = detect_swings(
    df,
    lookback=5
)

# Display the detected swings
swings = df[
    (df["swing_high"] == True) |
    (df["swing_low"] == True)
]

print("\n===== SWING DETECTION RESULTS =====")

print(
    swings[
        [
            "time",
            "high",
            "low",
            "swing_high",
            "swing_low"
        ]
    ].tail(30)
)

print("\n===== SUMMARY =====")

print(
    "Swing Highs:",
    df["swing_high"].sum()
)

print(
    "Swing Lows:",
    df["swing_low"].sum()
)

print(
    "Total candles:",
    len(df)
)