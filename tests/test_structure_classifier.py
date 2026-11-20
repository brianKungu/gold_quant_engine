import pandas as pd

from strategies.structure_classifier import (
    classify_market_structure
)


def create_test_pivots():

    return pd.DataFrame([
        # HIGH tests
        {
            "pivot_time": "2026-01-01 00:00",
            "confirmation_time": "2026-01-01 00:15",
            "pivot_type": "HIGH",
            "pivot_price": 100.00,
            "confirmation_index": 1,
            "confirmation_atr": 2.0
        },
        {
            "pivot_time": "2026-01-01 00:30",
            "confirmation_time": "2026-01-01 00:45",
            "pivot_type": "HIGH",
            "pivot_price": 100.15,
            "confirmation_index": 3,
            "confirmation_atr": 2.0
        },
        {
            "pivot_time": "2026-01-01 01:00",
            "confirmation_time": "2026-01-01 01:15",
            "pivot_type": "HIGH",
            "pivot_price": 100.30,
            "confirmation_index": 5,
            "confirmation_atr": 2.0
        },
        {
            "pivot_time": "2026-01-01 01:30",
            "confirmation_time": "2026-01-01 01:45",
            "pivot_type": "HIGH",
            "pivot_price": 99.90,
            "confirmation_index": 7,
            "confirmation_atr": 2.0
        },

        # LOW tests
        {
            "pivot_time": "2026-01-01 02:00",
            "confirmation_time": "2026-01-01 02:15",
            "pivot_type": "LOW",
            "pivot_price": 90.00,
            "confirmation_index": 9,
            "confirmation_atr": 2.0
        },
        {
            "pivot_time": "2026-01-01 02:30",
            "confirmation_time": "2026-01-01 02:45",
            "pivot_type": "LOW",
            "pivot_price": 90.10,
            "confirmation_index": 11,
            "confirmation_atr": 2.0
        },
        {
            "pivot_time": "2026-01-01 03:00",
            "confirmation_time": "2026-01-01 03:15",
            "pivot_type": "LOW",
            "pivot_price": 89.70,
            "confirmation_index": 13,
            "confirmation_atr": 2.0
        },
        {
            "pivot_time": "2026-01-01 03:30",
            "confirmation_time": "2026-01-01 03:45",
            "pivot_type": "LOW",
            "pivot_price": 90.10,
            "confirmation_index": 15,
            "confirmation_atr": 2.0
        },

        # ATR averaging test
        {
            "pivot_time": "2026-01-01 04:00",
            "confirmation_time": "2026-01-01 04:15",
            "pivot_type": "HIGH",
            "pivot_price": 100.25,
            "confirmation_index": 17,
            "confirmation_atr": 4.0
        }
    ])


def run_tests():

    pivots = create_test_pivots()

    result = classify_market_structure(pivots)

    expected = [
        "INITIAL_HIGH",
        "EQH",
        "HH",
        "LH",
        "INITIAL_LOW",
        "EQL",
        "LL",
        "HL",
        "HH"
    ]

    actual = result["structure"].tolist()

    print("\nEXPECTED STRUCTURES:")
    print(expected)

    print("\nACTUAL STRUCTURES:")
    print(actual)

    assert actual == expected, (
        "Structure classification failed."
    )

    assert result["confirmation_index"].is_monotonic_increasing

    assert result["trend_state"].notna().all()

    print("\nAll synthetic classifier tests passed.")


if __name__ == "__main__":
    run_tests()