import numpy as np
import pandas as pd

from analysis.wyckoff import compute_phase


def test_compute_phase_detects_markup_breakout():
    n = 80
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    closes = np.concatenate([
        100 + np.random.RandomState(1).normal(0, 0.3, 60),
        np.linspace(100.5, 110, 20),
    ])
    vols = np.concatenate([np.full(60, 1000), np.linspace(1000, 4000, 20)])
    df = pd.DataFrame({"high": closes + 0.5, "low": closes - 0.5, "close": closes, "volume": vols}, index=dates)
    result = compute_phase(df)
    assert result["phase"] == "markup"
    assert result["since"] is not None


def test_compute_phase_undefined_when_insufficient_history():
    df = pd.DataFrame({
        "high": [101.0] * 10, "low": [99.0] * 10, "close": [100.0] * 10, "volume": [1000.0] * 10,
    })
    result = compute_phase(df)
    assert result["phase"] == "undefined"
    assert result["since"] is None
