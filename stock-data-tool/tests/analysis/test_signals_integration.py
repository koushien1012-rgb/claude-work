import numpy as np
import pandas as pd

from analysis.signals import outlook
from analysis.technical import compute_indicators


def _make_uptrend_df(n=300):
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 5000, n),
    }, index=dates)


def test_outlook_includes_new_score_components():
    df = _make_uptrend_df(300)
    result = outlook(compute_indicators(df), df)
    assert "candlestick_pattern" in result["short_term"]["details"]
    assert "fibonacci_position" in result["short_term"]["details"]
    assert "dow_trend_daily" in result["mid_term"]["details"]
    assert "wyckoff_phase" in result["mid_term"]["details"]
    assert "dow_trend_weekly" in result["long_term"]["details"]
    assert "volume_profile_position" in result["long_term"]["details"]


def test_outlook_scores_stay_in_valid_range():
    df = _make_uptrend_df(300)
    result = outlook(compute_indicators(df), df)
    for term in ("short_term", "mid_term", "long_term"):
        assert -1.0 <= result[term]["score"] <= 1.0
        for component_score in result[term]["details"].values():
            assert -1.0 <= component_score <= 1.0


def test_uptrend_produces_positive_mid_and_long_scores():
    df = _make_uptrend_df(300)
    result = outlook(compute_indicators(df), df)
    assert result["mid_term"]["score"] > 0
    assert result["long_term"]["score"] > 0
