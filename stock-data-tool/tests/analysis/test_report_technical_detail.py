from unittest.mock import patch

import numpy as np
import pandas as pd

from analysis.report import generate_report


def _fake_df(n=300):
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 5000, n),
    }, index=dates)


def test_generate_report_includes_raw_technical_detail():
    df = _fake_df()
    with patch("analysis.report.get_daily", return_value=df), \
         patch("analysis.report.get_macro_daily", return_value=df), \
         patch("analysis.report.get_tdnet_disclosures", return_value=[]), \
         patch("analysis.report.get_yfinance_news", return_value=[]), \
         patch("analysis.report.get_next_earnings_date", return_value=None):
        report = generate_report("TESTX", name="Test Co", sector="Technology")

    tech = report["technical"]
    assert "dow_theory" in tech
    assert "daily" in tech["dow_theory"] and "weekly" in tech["dow_theory"]
    assert "wyckoff_phase" in tech
    assert "candlestick_pattern" in tech
    assert "fibonacci_position" in tech
    assert "volume_profile" in tech
    # existing short/mid/long-term summary must still be present (backward compatible)
    assert "short_term" in tech and "mid_term" in tech and "long_term" in tech
