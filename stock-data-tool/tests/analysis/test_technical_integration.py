import numpy as np
import pandas as pd

from analysis.technical import compute_indicators


def _make_long_history_df(n=300):
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 5000, n),
    }, index=dates)


def test_compute_indicators_includes_new_keys():
    df = _make_long_history_df(300)
    indicators = compute_indicators(df)
    for key in ("dow_daily", "dow_weekly", "wyckoff", "candlestick", "fibonacci", "volume_profile"):
        assert key in indicators


def test_dow_weekly_falls_back_to_sideways_on_short_history():
    df = _make_long_history_df(20)  # too short for a meaningful weekly resample
    indicators = compute_indicators(df)
    assert indicators["dow_weekly"]["trend"] in ("sideways", "up", "down")
    assert isinstance(indicators["dow_weekly"]["last_swings"], list)
