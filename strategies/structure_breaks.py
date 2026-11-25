import pandas as pd


def detect_structure_breaks(candles, protected_pivots):

    """
    Detect BOS and CHoCH using completed candle closes.

    Important:
    A pivot is only available from the candle AFTER
    its confirmation candle.

    This prevents look-ahead bias.

    Events:
        BULLISH_BOS
        BEARISH_BOS
        BULLISH_CHOCH
        BEARISH_CHOCH
    """

    required_candle_columns = [
        "time",
        "close"
    ]

    required_pivot_columns = [
        "pivot_type",
        "pivot_price",
        "confirmation_index",
        "structure_direction",
        "protected_high",
        "protected_low",
        "protected_high_index",
        "protected_low_index"
    ]

    for column in required_candle_columns:

        if column not in candles.columns:
            raise ValueError(
                f"Missing candle column: {column}"
            )

    for column in required_pivot_columns:

        if column not in protected_pivots.columns:
            raise ValueError(
                f"Missing pivot column: {column}"
            )

    if candles.empty or protected_pivots.empty:
        raise ValueError("Input datasets cannot be empty.")

    data = candles.reset_index(drop=True).copy()

    pivots = protected_pivots.sort_values(
        "confirmation_index"
    ).reset_index(drop=True)

    if data["time"].duplicated().any():
        raise ValueError("Duplicate candle timestamps.")

    if not data["time"].is_monotonic_increasing:
        raise ValueError("Candles are not chronological.")

    if pivots["confirmation_index"].duplicated().any():
        raise ValueError("Duplicate pivot confirmation indices.")

    if not pivots["pivot_type"].isin(["HIGH", "LOW"]).all():
        raise ValueError("Invalid pivot type.")

    if not pivots["confirmation_index"].map(
        lambda x: float(x).is_integer()
    ).all():
        raise ValueError("Confirmation indices must be integers.")

    if (
        (pivots["confirmation_index"] < 0) |
        (pivots["confirmation_index"] >= len(data))
    ).any():
        raise ValueError("Invalid pivot confirmation index.")

    # ======================================
    # MARKET STATE
    # ======================================

    latest_high = None
    latest_low = None

    protected_high = None
    protected_low = None

    protected_high_index = None
    protected_low_index = None

    last_seen_high_protection = None
    last_seen_low_protection = None

    bias = "UNDEFINED"

    # After CHoCH, wait for a newly confirmed
    # protected level before establishing direction again.
    transition_lock = False

    # Prevent repeated signals from the same broken level.
    broken_levels = set()

    events = []

    pivot_pointer = 0

    # ======================================
    # PROCESS COMPLETED CANDLES
    # ======================================

    for candle_index, candle in data.iterrows():

        close = float(candle["close"])

        # ----------------------------------
        # UPDATE AVAILABLE PIVOTS
        # ----------------------------------

        while (
            pivot_pointer < len(pivots)
            and pivots.loc[
                pivot_pointer, "confirmation_index"
            ] < candle_index
        ):

            pivot = pivots.loc[pivot_pointer]

            pivot_type = pivot["pivot_type"]

            pivot_price = float(pivot["pivot_price"])

            confirmation_index = int(
                pivot["confirmation_index"]
            )

            # Update latest confirmed swing high.
            if pivot_type == "HIGH":

                latest_high = {
                    "price": pivot_price,
                    "index": confirmation_index
                }

            # Update latest confirmed swing low.
            else:

                latest_low = {
                    "price": pivot_price,
                    "index": confirmation_index
                }

            # Update active protected levels.
            protected_high = pivot["protected_high"]

            protected_low = pivot["protected_low"]

            protected_high_index = pivot["protected_high_index"]

            protected_low_index = pivot["protected_low_index"]

            # ----------------------------------
            # ESTABLISH OR RESTORE MARKET BIAS
            # ----------------------------------

            if pd.notna(protected_low_index):

                protected_low_index = int(
                    protected_low_index
                )

            else:

                protected_low_index = None

            if pd.notna(protected_high_index):

                protected_high_index = int(
                    protected_high_index
                )

            else:

                protected_high_index = None

            new_bullish_protection = (
                protected_low_index is not None
                and protected_low_index != last_seen_low_protection
            )

            new_bearish_protection = (
                protected_high_index is not None
                and protected_high_index != last_seen_high_protection
            )

            if protected_low_index is not None:

                last_seen_low_protection = protected_low_index

            if protected_high_index is not None:

                last_seen_high_protection = protected_high_index

            if (
                new_bullish_protection
                and pivot["structure_direction"] == "BULLISH"
            ):

                bias = "BULLISH"
                transition_lock = False

            elif (
                new_bearish_protection
                and pivot["structure_direction"] == "BEARISH"
            ):

                bias = "BEARISH"
                transition_lock = False

            pivot_pointer += 1

        # ----------------------------------
        # STRUCTURAL BREAK DETECTION
        # ----------------------------------

        if transition_lock:
            continue

        event = None
        level_type = None
        level_price = None
        level_index = None

        previous_bias = bias

        # ==================================
        # BULLISH MARKET
        # ==================================

        if bias == "BULLISH":

            # CHoCH takes priority over BOS.
            if (
                protected_low is not None
                and pd.notna(protected_low)
                and close < float(protected_low)
            ):

                level_type = "PROTECTED_LOW"

                level_price = float(protected_low)

                level_index = protected_low_index

                event = "BEARISH_CHOCH"

            elif latest_high is not None:

                if close > latest_high["price"]:

                    level_type = "SWING_HIGH"

                    level_price = latest_high["price"]

                    level_index = latest_high["index"]

                    event = "BULLISH_BOS"

        # ==================================
        # BEARISH MARKET
        # ==================================

        elif bias == "BEARISH":

            # CHoCH takes priority over BOS.
            if (
                protected_high is not None
                and pd.notna(protected_high)
                and close > float(protected_high)
            ):

                level_type = "PROTECTED_HIGH"

                level_price = float(protected_high)

                level_index = protected_high_index

                event = "BULLISH_CHOCH"

            elif latest_low is not None:

                if close < latest_low["price"]:

                    level_type = "SWING_LOW"

                    level_price = latest_low["price"]

                    level_index = latest_low["index"]

                    event = "BEARISH_BOS"

        # ==================================
        # RECORD EVENT
        # ==================================

        if event is not None:

            level_key = (
                level_type,
                level_index
            )

            if level_key in broken_levels:
                continue

            broken_levels.add(level_key)

            # CHoCH changes the engine to transitional.
            if "CHOCH" in event:

                bias = "TRANSITIONAL"

                transition_lock = True

            events.append({

                "event_time": candle["time"],

                "candle_index": candle_index,

                "event_type": event,

                "broken_level_type": level_type,

                "broken_level_price": level_price,

                "level_confirmation_index": level_index,

                "bias_before": previous_bias,

                "bias_after": bias,

                "earliest_execution_index": candle_index + 1

            })

    return pd.DataFrame(
        events,
        columns=[
            "event_time",
            "candle_index",
            "event_type",
            "broken_level_type",
            "broken_level_price",
            "level_confirmation_index",
            "bias_before",
            "bias_after",
            "earliest_execution_index"
        ]
    )