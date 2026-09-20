from unittest.mock import patch

import numpy as np
import pandas as pd

from screener.scan import scan_universe


def _fake_download(tickers, **kwargs):
    n = 300
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    df = pd.DataFrame({
        "Open": closes, "High": closes + 1, "Low": closes - 1, "Close": closes, "Volume": np.linspace(1000, 5000, n),
    }, index=dates)
    return df  # single ticker path (len(batch) == 1 branch in scan_universe)


def test_scan_universe_includes_dow_daily_trend_column():
    with patch("screener.scan.yf.download", side_effect=_fake_download):
        result = scan_universe(["TESTX"], period="1y", batch_size=1)
    assert "dow_daily_trend" in result.columns
    assert result.iloc[0]["dow_daily_trend"] in ("up", "down", "sideways")
