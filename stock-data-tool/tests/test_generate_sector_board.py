from unittest.mock import patch

import pandas as pd

import generate_sector_board as mod


def _row(ticker="AAPL", short=0.2, mid=0.2, long=0.2):
    return pd.Series({
        "ticker": ticker, "name": "Apple Inc.", "sector": "Technology",
        "price": 250.0, "market_cap": 3_000_000_000_000.0,
        "short_score": short, "mid_score": mid, "long_score": long,
    })


def test_pick_to_dict_includes_earnings_date_and_business_summary():
    mod._business_summary_ja_cached.cache_clear()
    mod._next_earnings_date_cached.cache_clear()
    mod._name_ja_cached.cache_clear()
    with patch.object(mod, "get_next_earnings_date", return_value="2026-10-30"), \
         patch.object(mod, "get_business_summary_en", return_value="Apple makes phones."), \
         patch.object(mod, "business_summary_ja", return_value="アップルはスマートフォンを製造しています。"), \
         patch.object(mod, "translate_to_ja", return_value="アップル"):
        entry = mod._pick_to_dict(_row())

    assert entry["next_earnings_date"] == "2026-10-30"
    assert entry["business_summary_ja"] == "アップルはスマートフォンを製造しています。"
    assert entry["name_ja"] == "アップル"


def test_pick_to_dict_skips_name_translation_for_jp_tickers():
    mod._name_ja_cached.cache_clear()
    row = pd.Series({
        "ticker": "7011.T", "name": "三菱重工業", "sector": "Machinery",
        "price": 3879.0, "market_cap": 1_000_000_000_000.0,
        "short_score": 0.1, "mid_score": 0.1, "long_score": 0.1,
    })
    with patch.object(mod, "get_next_earnings_date", return_value=None), \
         patch.object(mod, "get_business_summary_en", return_value=None), \
         patch.object(mod, "translate_to_ja") as mock_translate:
        entry = mod._pick_to_dict(row)

    assert entry["name_ja"] is None
    mock_translate.assert_not_called()


def test_pick_to_dict_fetches_each_ticker_at_most_once_per_run():
    # AAPL can legitimately appear as a top-N pick in more than one category/sector within
    # a single run; the per-run memoization must prevent duplicate network calls for it.
    mod._business_summary_ja_cached.cache_clear()
    mod._next_earnings_date_cached.cache_clear()
    mod._name_ja_cached.cache_clear()
    with patch.object(mod, "get_next_earnings_date", return_value="2026-10-30") as mock_earnings, \
         patch.object(mod, "get_business_summary_en", return_value="Apple makes phones.") as mock_summary, \
         patch.object(mod, "business_summary_ja", return_value="要約"), \
         patch.object(mod, "translate_to_ja", return_value="アップル") as mock_name:
        mod._pick_to_dict(_row())
        mod._pick_to_dict(_row())

    mock_earnings.assert_called_once_with("AAPL")
    mock_summary.assert_called_once_with("AAPL")
    mock_name.assert_called_once_with("Apple Inc.")
