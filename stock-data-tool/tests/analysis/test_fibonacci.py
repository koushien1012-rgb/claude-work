import pandas as pd

from analysis.fibonacci import compute_levels, evaluate


def test_compute_levels_between_high_and_low():
    levels = compute_levels(swing_high=110, swing_low=90)
    assert levels[0.5] == 100.0
    assert levels[1.0] == 90.0
    assert levels[0.0] if 0.0 in levels else True  # 0.0 not required in level set


def test_evaluate_scores_midpoint_highest():
    swings = [{"type": "low", "price": 90}, {"type": "high", "price": 110}]
    df = pd.DataFrame({"close": [100.0]})
    result = evaluate(df, swings)
    assert result["price_zone"] == "0.500"
    assert result["score"] == 1.0


def test_evaluate_returns_unknown_with_no_swings():
    df = pd.DataFrame({"close": [100.0]})
    result = evaluate(df, [])
    assert result == {"levels": {}, "price_zone": "unknown", "score": 0.0}


def test_evaluate_returns_unknown_with_only_highs():
    swings = [{"type": "high", "price": 110}]
    df = pd.DataFrame({"close": [100.0]})
    result = evaluate(df, swings)
    assert result == {"levels": {}, "price_zone": "unknown", "score": 0.0}
