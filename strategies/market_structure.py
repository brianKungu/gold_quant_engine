import pandas as pd


def detect_swings(df, lookback=5):
    """
    Detect confirmed swing highs and swing lows.

    A swing high is a candle whose high is greater than
    the highs of the candles immediately before and after it.

    A swing low is the opposite.

    Important:
    Because we use candles on BOTH sides of the candidate
    candle, the swing is only confirmed after `lookback`
    subsequent candles have occurred.

    This prevents look-ahead bias.
    """

    df = df.copy()

    df["swing_high"] = False
    df["swing_low"] = False

    for i in range(
        lookback,
        len(df) - lookback
    ):

        current_high = df["high"].iloc[i]
        current_low = df["low"].iloc[i]

        previous_highs = df[
            "high"
        ].iloc[
            i - lookback:i
        ]

        following_highs = df[
            "high"
        ].iloc[
            i + 1:i + lookback + 1
        ]

        previous_lows = df[
            "low"
        ].iloc[
            i - lookback:i
        ]

        following_lows = df[
            "low"
        ].iloc[
            i + 1:i + lookback + 1
        ]

        # Swing high
        if (
            current_high > previous_highs.max()
            and
            current_high > following_highs.max()
        ):

            df.loc[
                df.index[i],
                "swing_high"
            ] = True

        # Swing low
        if (
            current_low < previous_lows.min()
            and
            current_low < following_lows.min()
        ):

            df.loc[
                df.index[i],
                "swing_low"
            ] = True

    return df


def build_alternating_pivots(df, lookback=5):
    """
    Convert raw swing detections into an alternating
    sequence of HIGH and LOW pivots.

    Rules:
    - Consecutive HIGHs: keep the highest.
    - Consecutive LOWs: keep the lowest.
    - Candles classified as both HIGH and LOW are excluded.
    - Each pivot records when it became confirmed.
    """

    df = df.copy().reset_index(drop=True)

    # Identify ambiguous candles
    both = df["swing_high"] & df["swing_low"]

    # Exclude ambiguous candles
    candidates = df[
        (df["swing_high"] | df["swing_low"]) & (~both)
    ].copy()

    pivots = []

    for position, row in candidates.iterrows():

        if row["swing_high"]:
            pivot_type = "HIGH"
            pivot_price = row["high"]

        else:
            pivot_type = "LOW"
            pivot_price = row["low"]

        # Confirmation occurs after lookback subsequent candles
        confirmation_position = position + lookback

        if confirmation_position >= len(df):
            continue

        pivot = {
            "pivot_time": row["time"],
            "confirmation_time": df.loc[
                confirmation_position, "time"
            ],
            "pivot_type": pivot_type,
            "pivot_price": pivot_price
        }

        # First pivot
        if len(pivots) == 0:
            pivots.append(pivot)
            continue

        previous = pivots[-1]

        # Same type: retain only the more extreme pivot
        if pivot_type == previous["pivot_type"]:

            if pivot_type == "HIGH":
                if pivot_price > previous["pivot_price"]:
                    pivots[-1] = pivot

            else:
                if pivot_price < previous["pivot_price"]:
                    pivots[-1] = pivot

        # Opposite type: append the new pivot
        else:
            pivots.append(pivot)

    return pd.DataFrame(pivots)
