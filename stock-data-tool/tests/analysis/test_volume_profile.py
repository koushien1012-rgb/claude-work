import numpy as np
import pandas as pd

from analysis.volume_profile import compute_profile


def test_poc_near_concentrated_volume_price():
    rng = np.random.RandomState(0)
    prices = np.concatenate([rng.normal(105, 1, 80), rng.uniform(95, 115, 20)])
    volumes = np.concatenate([np.full(80, 5000), np.full(20, 500)])
    df = pd.DataFrame({"close": prices, "volume": volumes})
    result = compute_profile(df)
    assert 103 < result["poc"] < 107
    assert result["value_area"][0] < result["poc"] < result["value_area"][1]


def test_flat_price_series_no_division_by_zero():
    df = pd.DataFrame({"close": [100.0] * 10, "volume": [1000.0] * 10})
    result = compute_profile(df)
    assert result["poc"] == 100.0
    assert result["value_area"] == (100.0, 100.0)
    assert result["price_vs_poc"] == 0.0


def test_empty_df_returns_none_poc():
    df = pd.DataFrame({"close": [], "volume": []})
    result = compute_profile(df)
    assert result["poc"] is None
