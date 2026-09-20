import pandas as pd

from analysis.chart_data import build_chart_data


def _sample_df():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "open": range(100, 110), "high": range(101, 111), "low": range(99, 109),
        "close": range(100, 110), "volume": [1000] * 10,
    }, index=dates)


def test_build_chart_data_shape():
    df = _sample_df()
    swings = [
        {"date": df.index[2], "price": 101.0, "type": "low"},
        {"date": df.index[7], "price": 108.0, "type": "high"},
    ]
    fib_levels = {0.5: 104.5, 0.618: 103.3}
    candlestick = {"pattern": "hammer", "direction": 1, "bar_index": 9}
    wyckoff_result = {"phase": "markup", "since": df.index[5]}

    chart = build_chart_data(df, swings, fib_levels, candlestick, wyckoff_result, window=180)

    assert len(chart["ohlcv"]) == 10
    assert chart["ohlcv"][0]["date"] == "2024-01-01"
    assert len(chart["annotations"]["swings"]) == 2
    assert len(chart["annotations"]["fibonacci_levels"]) == 2
    assert len(chart["annotations"]["candlestick_markers"]) == 1
    assert len(chart["annotations"]["wyckoff_zones"]) == 1
    assert chart["annotations"]["wyckoff_zones"][0]["phase"] == "markup"


def test_build_chart_data_without_pattern_or_wyckoff():
    df = _sample_df()
    chart = build_chart_data(df, swings=[], fibonacci_levels={}, candlestick={"pattern": None, "direction": 0, "bar_index": None})
    assert chart["annotations"]["candlestick_markers"] == []
    assert chart["annotations"]["wyckoff_zones"] == []


def test_build_chart_data_truncates_to_window():
    df = _sample_df()
    chart = build_chart_data(df, swings=[], fibonacci_levels={}, candlestick={"pattern": None, "direction": 0, "bar_index": None}, window=5)
    assert len(chart["ohlcv"]) == 5
    assert chart["ohlcv"][0]["date"] == "2024-01-06"
