import MetaTrader5 as mt5

# ===================================
# Trading Symbol
# ===================================

SYMBOL = "XAUUSD"

# ===================================
# Timeframes
# ===================================

TIMEFRAMES = {
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4
}

# ===================================
# Data Range
# ===================================

START_YEAR = 2020

# ======================================
# GOLD QUANT ENGINE SETTINGS
# ======================================

# Market configuration
SYMBOL = "XAUUSD"
TIMEFRAME = "M15"

# ATR configuration
ATR_PERIOD = 14
ATR_MULTIPLIER = 2.0

# Market structure configuration
EQUAL_LEVEL_TOLERANCE = 0.10