import numpy as np
import pandas as pd

from analysis.dow_theory import analyze, classify_trend, find_swings


def _make_trending_df(n=60, direction=1):
    t = np.arange(n)
    cycle = 10
    drift = direction * 1.2 * t
    zigzag = 5 * np.sin(2 * np.pi * t / cycle)
    closes = 100 + drift + zigzag
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 0.3, "low": closes - 0.3, "close": closes,
        "volume": np.linspace(1000, 3000, n),
    }, index=dates)


def test_find_swings_detects_local_extrema():
    df = _make_trending_df(60, direction=1)
    swings = find_swings(df, window=5)
    assert len(swings) > 0
    assert all(s["type"] in ("high", "low") for s in swings)


def test_classify_trend_up_on_higher_highs_and_lows():
    df = _make_trending_df(60, direction=1)
    swings = find_swings(df, window=5)
    assert classify_trend(swings) == "up"


def test_classify_trend_down_on_lower_highs_and_lows():
    df = _make_trending_df(60, direction=-1)
    swings = find_swings(df, window=5)
    assert classify_trend(swings) == "down"


def test_classify_trend_sideways_when_insufficient_swings():
    assert classify_trend([{"type": "high", "price": 100.0}]) == "sideways"


def test_analyze_returns_expected_shape():
    df = _make_trending_df(60, direction=1)
    result = analyze(df, window=5)
    assert result["trend"] == "up"
    assert isinstance(result["confirmed_by_volume"], bool)
    assert len(result["last_swings"]) <= 6
