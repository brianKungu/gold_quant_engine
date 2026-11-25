import pandas as pd

from strategies.structure_breaks import (
    detect_structure_breaks
)


def create_test_data():

    # ======================================
    # CANDLE DATA
    # ======================================

    candles = pd.DataFrame({

        "time": pd.date_range(
            start="2026-01-01",
            periods=8,
            freq="15min"
        ),

        "open": [
            112, 112, 112, 114, 114, 116, 116, 104
        ],

        "high": [
            113, 113, 117, 117, 118, 117, 116, 105
        ],

        "low": [
            111, 111, 110, 110, 112, 113, 103, 102
        ],

        "close": [
            112, 112, 116, 114, 116, 116, 104, 103
        ]

    })

    # ======================================
    # CONFIRMED PIVOTS
    # ======================================

    pivots = pd.DataFrame([

        {
            "pivot_type": "HIGH",
            "pivot_price": 110,
            "confirmation_index": 0,
            "structure_direction": "UNDEFINED",
            "protected_high": None,
            "protected_low": None,
            "protected_high_index": None,
            "protected_low_index": None
        },

        {
            "pivot_type": "LOW",
            "pivot_price": 105,
            "confirmation_index": 1,
            "structure_direction": "UNDEFINED",
            "protected_high": None,
            "protected_low": None,
            "protected_high_index": None,
            "protected_low_index": None
        },

        {
            "pivot_type": "HIGH",
            "pivot_price": 115,
            "confirmation_index": 2,
            "structure_direction": "BULLISH",
            "protected_high": None,
            "protected_low": 105,
            "protected_high_index": None,
            "protected_low_index": 1
        }

    ])

    return candles, pivots


def run_tests():

    candles, pivots = create_test_data()

    events = detect_structure_breaks(
        candles,
        pivots
    )

    print("\nSTRUCTURAL BREAK TEST RESULTS")

    print(events.to_string(index=False))

    # We expect exactly two events.
    assert len(events) == 2

    # First event must be bullish BOS.
    assert events.iloc[0]["event_type"] == "BULLISH_BOS"

    # It must occur at candle index 4.
    assert events.iloc[0]["candle_index"] == 4

    # Second event must be bearish CHoCH.
    assert events.iloc[1]["event_type"] == "BEARISH_CHOCH"

    # It must occur at candle index 6.
    assert events.iloc[1]["candle_index"] == 6

    # CHoCH should move the engine into transition.
    assert events.iloc[1]["bias_after"] == "TRANSITIONAL"

    # Execution cannot happen on the signal candle.
    assert (
        events["earliest_execution_index"]
        == events["candle_index"] + 1
    ).all()

    print("\nAll structural break tests passed.")


if __name__ == "__main__":
    run_tests()