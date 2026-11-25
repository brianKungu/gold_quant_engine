import pandas as pd


def identify_protected_levels(classified_pivots):

    required_columns = [
        "pivot_time",
        "confirmation_time",
        "pivot_type",
        "pivot_price",
        "confirmation_index",
        "structure"
    ]

    for column in required_columns:
        if column not in classified_pivots.columns:
            raise ValueError(f"Missing required column: {column}")

    if classified_pivots.empty:
        raise ValueError("Pivot dataset is empty.")

    data = classified_pivots.copy()

    data = data.sort_values(
        "confirmation_index"
    ).reset_index(drop=True)

    if data["confirmation_index"].duplicated().any():
        raise ValueError("Duplicate confirmation indices.")

    if not data["pivot_type"].isin(["HIGH", "LOW"]).all():
        raise ValueError("Invalid pivot type.")

    # Pending candidate levels
    pending_hl = None
    pending_lh = None

    # Confirmed protected levels
    protected_low = None
    protected_high = None

    protected_low_index = None
    protected_high_index = None

    direction = "UNDEFINED"

    results = []

    for _, row in data.iterrows():

        structure = row["structure"]

        price = float(row["pivot_price"])

        index = int(row["confirmation_index"])

        # ==================================
        # HIGH PIVOT
        # ==================================

        if row["pivot_type"] == "HIGH":

            # A HIGH pivot resolves a pending HL.

            if pending_hl is not None:

                if structure == "HH":

                    protected_low = pending_hl["price"]

                    protected_low_index = pending_hl["index"]

                    protected_high = None
                    protected_high_index = None

                    direction = "BULLISH"

                # LH, EQH or another HIGH classification
                # invalidates the pending HL.

                pending_hl = None

            # A lower high becomes a bearish candidate.

            if structure == "LH":

                pending_lh = {
                    "price": price,
                    "index": index
                }

            else:

                pending_lh = None

            # A higher high without a valid preceding HL
            # does not establish a new protected low.

            if structure == "HH" and direction == "UNDEFINED":
                direction = "TRANSITIONAL"

        # ==================================
        # LOW PIVOT
        # ==================================

        elif row["pivot_type"] == "LOW":

            # A LOW pivot resolves a pending LH.

            if pending_lh is not None:

                if structure == "LL":

                    protected_high = pending_lh["price"]

                    protected_high_index = pending_lh["index"]

                    protected_low = None
                    protected_low_index = None

                    direction = "BEARISH"

                # HL, EQL or another LOW classification
                # invalidates the pending LH.

                pending_lh = None

            # A higher low becomes a bullish candidate.

            if structure == "HL":

                pending_hl = {
                    "price": price,
                    "index": index
                }

            else:

                pending_hl = None

            if structure == "LL" and direction == "UNDEFINED":
                direction = "TRANSITIONAL"

        results.append({

            "protected_high": protected_high,

            "protected_low": protected_low,

            "protected_high_index": protected_high_index,

            "protected_low_index": protected_low_index,

            "structure_direction": direction

        })

    result = pd.concat(
        [
            data,
            pd.DataFrame(results)
        ],
        axis=1
    )

    return result