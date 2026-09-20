import pandas as pd

from analysis.candlestick import detect_pattern


def test_detects_bullish_engulfing():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 98, "close": 99},
        {"open": 98.5, "high": 103, "low": 98, "close": 102},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": "bullish_engulfing", "direction": 1, "bar_index": 1}


def test_detects_hammer():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 95, "close": 100.5},
        {"open": 99, "high": 100, "low": 90, "close": 99.5},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": "hammer", "direction": 1, "bar_index": 1}


def test_detects_doji():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 99, "close": 100},
        {"open": 100, "high": 105, "low": 95, "close": 100.05},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": "doji", "direction": 0, "bar_index": 1}


def test_no_pattern_returns_none():
    df = pd.DataFrame([
        {"open": 100, "high": 102, "low": 99, "close": 101},
        {"open": 101, "high": 103, "low": 100, "close": 102},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": None, "direction": 0, "bar_index": None}


def test_insufficient_bars_returns_none():
    df = pd.DataFrame([{"open": 100, "high": 101, "low": 99, "close": 100}])
    result = detect_pattern(df)
    assert result == {"pattern": None, "direction": 0, "bar_index": None}
