import pandas as pd


def classify_market_structure(pivots):
    """
    Classify confirmed ZigZag pivots into:

    HIGH:
        HH = Higher High
        LH = Lower High
        EQH = Equal High

    LOW:
        HL = Higher Low
        LL = Lower Low
        EQL = Equal Low

    Trend states:
        BULLISH
        BEARISH
        TRANSITIONAL
        UNDEFINED

    Pivots are processed in confirmation order to prevent
    future information from influencing earlier classifications.
    """

    required_columns = [
        "pivot_time",
        "confirmation_time",
        "pivot_type",
        "pivot_price",
        "confirmation_index"
    ]

    for column in required_columns:
        if column not in pivots.columns:
            raise ValueError(
                f"Missing required column: {column}"
            )

    if pivots.empty:
        raise ValueError("Pivot dataset is empty.")

    data = pivots.copy()

    # Process pivots in the order they become confirmed.
    data = data.sort_values(
        ["confirmation_index", "pivot_index"]
        if "pivot_index" in data.columns
        else ["confirmation_index"]
    ).reset_index(drop=True)

    # Validate pivot types.
    if not data["pivot_type"].isin(["HIGH", "LOW"]).all():
        raise ValueError("Invalid pivot type detected.")

    # Confirmed pivots must have unique confirmation indices.
    if data["confirmation_index"].duplicated().any():
        raise ValueError(
            "Multiple pivots share a confirmation index."
        )

    previous_high = None
    previous_low = None

    latest_high_structure = None
    latest_low_structure = None

    classifications = []
    trend_states = []

    for _, row in data.iterrows():

        pivot_type = row["pivot_type"]
        price = float(row["pivot_price"])

        # ------------------------------
        # CLASSIFY HIGH PIVOTS
        # ------------------------------

        if pivot_type == "HIGH":

            if previous_high is None:
                structure = "INITIAL_HIGH"

            elif price > previous_high:
                structure = "HH"

            elif price < previous_high:
                structure = "LH"

            else:
                structure = "EQH"

            previous_high = price
            latest_high_structure = structure

        # ------------------------------
        # CLASSIFY LOW PIVOTS
        # ------------------------------

        else:

            if previous_low is None:
                structure = "INITIAL_LOW"

            elif price > previous_low:
                structure = "HL"

            elif price < previous_low:
                structure = "LL"

            else:
                structure = "EQL"

            previous_low = price
            latest_low_structure = structure

        classifications.append(structure)

        # ------------------------------
        # DETERMINE MARKET TREND
        # ------------------------------

        if (
            latest_high_structure == "HH"
            and latest_low_structure == "HL"
        ):
            trend = "BULLISH"

        elif (
            latest_high_structure == "LH"
            and latest_low_structure == "LL"
        ):
            trend = "BEARISH"

        elif (
            latest_high_structure is None
            or latest_low_structure is None
        ):
            trend = "UNDEFINED"

        else:
            trend = "TRANSITIONAL"

        trend_states.append(trend)

    data["structure"] = classifications
    data["trend_state"] = trend_states

    return data