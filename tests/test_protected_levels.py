import pandas as pd

from strategies.protected_levels import (
    identify_protected_levels
)


def create_test_data():

    rows = [

        ("LOW", 90, "INITIAL_LOW"),
        ("HIGH", 100, "INITIAL_HIGH"),

        # Valid bullish sequence
        ("LOW", 95, "HL"),
        ("HIGH", 105, "HH"),

        # Update bullish protection
        ("LOW", 98, "HL"),
        ("HIGH", 110, "HH"),

        # HL invalidated by LH
        ("LOW", 101, "HL"),
        ("HIGH", 108, "LH"),

        # Valid bearish sequence
        ("LOW", 99, "LL"),
        ("HIGH", 107, "LH"),
        ("LOW", 92, "LL"),

        # LH invalidated by EQL
        ("HIGH", 104, "LH"),
        ("LOW", 96, "EQL"),
        ("HIGH", 109, "HH"),

        # LH invalidated by HL
        ("LOW", 94, "LL"),
        ("HIGH", 103, "LH"),
        ("LOW", 96, "HL"),

        # HL invalidated by EQH
        ("HIGH", 105, "EQH"),
        ("LOW", 93, "EQL"),
        ("HIGH", 110, "HH")

    ]

    records = []

    for i, (pivot_type, price, structure) in enumerate(rows):

        records.append({

            "pivot_time": pd.Timestamp("2026-01-01") +
                          pd.Timedelta(minutes=30 * i),

            "confirmation_time": pd.Timestamp("2026-01-01") +
                                 pd.Timedelta(minutes=30 * i + 15),

            "pivot_type": pivot_type,

            "pivot_price": price,

            "confirmation_index": i + 1,

            "structure": structure

        })

    return pd.DataFrame(records)


def run_tests():

    pivots = create_test_data()

    result = identify_protected_levels(pivots)

    print("\nPROTECTED LEVEL TEST RESULTS")

    print(
        result[
            [
                "structure",
                "pivot_price",
                "protected_high",
                "protected_low",
                "structure_direction"
            ]
        ].to_string(index=False)
    )

    # Valid bullish confirmation
    assert result.loc[3, "protected_low"] == 95

    # Updated bullish protection
    assert result.loc[5, "protected_low"] == 98

    # HL invalidated by LH
    assert result.loc[7, "protected_low"] == 98

    # Valid bearish confirmation
    assert result.loc[10, "protected_high"] == 107

    # LH invalidated by EQL
    assert result.loc[13, "protected_high"] == 107

    # LH invalidated by HL
    assert result.loc[16, "protected_high"] == 107

    # HL invalidated by EQH
    assert pd.isna(result.loc[17, "protected_low"])

    # No stale HL should establish bullish protection
    assert pd.isna(result.loc[19, "protected_low"])

    # Bearish protection remains
    assert result.loc[19, "protected_high"] == 107

    assert result.loc[19, "structure_direction"] == "BEARISH"

    assert result["structure_direction"].notna().all()

    assert result["confirmation_index"].is_monotonic_increasing

    print("\nAll protected-level tests passed.")


if __name__ == "__main__":
    run_tests()