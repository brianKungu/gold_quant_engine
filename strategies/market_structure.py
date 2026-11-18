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

def detect_atr_zigzag(df, atr_column="atr", multiplier=1.5):
    """
    ATR-based ZigZag pivot detector.

    A pivot is confirmed only when price reverses by
    the specified ATR multiple.

    Confirmation uses completed candle data.

    The pivot's original time and its confirmation time
    are stored separately to prevent look-ahead bias.
    """

    required_columns = [
        "time", "high", "low", "close", atr_column
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing required column: {column}")

    if multiplier <= 0:
        raise ValueError("Multiplier must be greater than zero.")

    data = df.reset_index(drop=True)

    valid_positions = data.index[
        data[atr_column].notna() &
        (data[atr_column] > 0)
    ]

    if len(valid_positions) < 2:
        raise ValueError("Not enough valid ATR observations.")

    first_position = valid_positions[0]

    # Initial reference price
    anchor = float(data.loc[first_position, "close"])

    # Direction:
    #  0 = Not established
    #  1 = Tracking upward movement
    # -1 = Tracking downward movement

    direction = 0

    candidate_high = None
    candidate_high_index = None

    candidate_low = None
    candidate_low_index = None

    pivots = []

    for i in range(first_position + 1, len(data)):

        atr = data.loc[i, atr_column]

        if pd.isna(atr) or atr <= 0:
            continue

        threshold = float(atr) * multiplier

        high = float(data.loc[i, "high"])
        low = float(data.loc[i, "low"])
        close = float(data.loc[i, "close"])

        # ==================================
        # INITIAL DIRECTION DETECTION
        # ==================================

        if direction == 0:

            if close - anchor >= threshold:

                direction = 1

                candidate_high = high
                candidate_high_index = i

            elif anchor - close >= threshold:

                direction = -1

                candidate_low = low
                candidate_low_index = i

            continue

        # ==================================
        # UPWARD MOVEMENT
        # ==================================

        if direction == 1:

            # Track the highest price
            if high > candidate_high:

                candidate_high = high
                candidate_high_index = i

            # Confirm a high after sufficient reversal
            if candidate_high - close >= threshold:

                pivot_index = candidate_high_index

                pivots.append({
                    "pivot_time": data.loc[pivot_index, "time"],
                    "confirmation_time": data.loc[i, "time"],
                    "pivot_type": "HIGH",
                    "pivot_price": candidate_high,
                    "pivot_index": pivot_index,
                    "confirmation_index": i,
                    "confirmation_atr": atr,
                    "confirmation_threshold": threshold
                })

                # Start tracking a potential low.
                # Use the confirmation candle's close rather
                # than its intrabar low to avoid ambiguity.

                direction = -1

                candidate_low = close
                candidate_low_index = i

        # ==================================
        # DOWNWARD MOVEMENT
        # ==================================

        elif direction == -1:

            # Track the lowest price
            if low < candidate_low:

                candidate_low = low
                candidate_low_index = i

            # Confirm a low after sufficient reversal
            if close - candidate_low >= threshold:

                pivot_index = candidate_low_index

                pivots.append({
                    "pivot_time": data.loc[pivot_index, "time"],
                    "confirmation_time": data.loc[i, "time"],
                    "pivot_type": "LOW",
                    "pivot_price": candidate_low,
                    "pivot_index": pivot_index,
                    "confirmation_index": i,
                    "confirmation_atr": atr,
                    "confirmation_threshold": threshold
                })

                # Start tracking a potential high

                direction = 1

                candidate_high = close
                candidate_high_index = i

    return pd.DataFrame(
        pivots,
        columns=[
            "pivot_time",
            "confirmation_time",
            "pivot_type",
            "pivot_price",
            "pivot_index",
            "confirmation_index",
            "confirmation_atr",
            "confirmation_threshold"
        ]
    )
