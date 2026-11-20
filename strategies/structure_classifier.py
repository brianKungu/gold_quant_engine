import pandas as pd

from config.settings import EQUAL_LEVEL_TOLERANCE


def classify_market_structure(pivots):

    required_columns = [
        "pivot_time",
        "confirmation_time",
        "pivot_type",
        "pivot_price",
        "confirmation_index",
        "confirmation_atr"
    ]

    for column in required_columns:
        if column not in pivots.columns:
            raise ValueError(f"Missing required column: {column}")

    if pivots.empty:
        raise ValueError("Pivot dataset is empty.")

    if EQUAL_LEVEL_TOLERANCE < 0:
        raise ValueError("Equal level tolerance cannot be negative.")

    data = pivots.copy()

    data = data.sort_values(
        "confirmation_index"
    ).reset_index(drop=True)

    if not data["pivot_type"].isin(["HIGH", "LOW"]).all():
        raise ValueError("Invalid pivot type detected.")

    if data["confirmation_index"].duplicated().any():
        raise ValueError("Duplicate confirmation indices detected.")

    # Reference prices and their corresponding ATR values.
    previous_high = None
    previous_high_atr = None

    previous_low = None
    previous_low_atr = None

    latest_high_structure = None
    latest_low_structure = None

    classifications = []
    trend_states = []

    for _, row in data.iterrows():

        pivot_type = row["pivot_type"]
        price = float(row["pivot_price"])
        current_atr = float(row["confirmation_atr"])

        if pd.isna(current_atr) or current_atr <= 0:
            raise ValueError("Invalid confirmation ATR detected.")

        # ======================================
        # HIGH CLASSIFICATION
        # ======================================

        if pivot_type == "HIGH":

            if previous_high is None:

                structure = "INITIAL_HIGH"

                previous_high = price
                previous_high_atr = current_atr

            else:

                average_atr = (
                    current_atr + previous_high_atr
                ) / 2

                tolerance = (
                    average_atr * EQUAL_LEVEL_TOLERANCE
                )

                difference = price - previous_high

                if difference > tolerance:

                    structure = "HH"

                    previous_high = price
                    previous_high_atr = current_atr

                elif difference < -tolerance:

                    structure = "LH"

                    previous_high = price
                    previous_high_atr = current_atr

                else:

                    structure = "EQH"

                    # Do not move the reference level.
                    # This prevents equal-level drift.

            latest_high_structure = structure

        # ======================================
        # LOW CLASSIFICATION
        # ======================================

        else:

            if previous_low is None:

                structure = "INITIAL_LOW"

                previous_low = price
                previous_low_atr = current_atr

            else:

                average_atr = (
                    current_atr + previous_low_atr
                ) / 2

                tolerance = (
                    average_atr * EQUAL_LEVEL_TOLERANCE
                )

                difference = price - previous_low

                if difference > tolerance:

                    structure = "HL"

                    previous_low = price
                    previous_low_atr = current_atr

                elif difference < -tolerance:

                    structure = "LL"

                    previous_low = price
                    previous_low_atr = current_atr

                else:

                    structure = "EQL"

                    # Do not move the reference level.

            latest_low_structure = structure

        classifications.append(structure)

        # ======================================
        # TREND CLASSIFICATION
        # ======================================

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