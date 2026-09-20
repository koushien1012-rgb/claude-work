import json
from unittest.mock import patch

import numpy as np
import pandas as pd

from generate_daily_watchlist import _build_market_block, _sanitize


def _fake_ohlcv_df(n=30):
    t = np.arange(n)
    closes = 100 + 0.2 * t
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 2000, n),
    }, index=dates)


def _fake_report(ticker: str) -> dict:
    """Mirrors the real report["technical"] schema.

    Field names/types match analysis/fibonacci.evaluate(), analysis/candlestick.detect_pattern()
    and analysis/volume_profile.compute_profile() -- notably fibonacci levels are keyed by
    float, the zone field is "price_zone" (not "position"), candlestick direction is always an
    int in {-1, 0, 1} (never None), and volume_profile carries "price_vs_poc" and "value_area".
    """
    swings = [{"date": pd.Timestamp("2024-01-05"), "price": 101.0, "type": "low"}]
    return {
        "ticker": ticker,
        "name": f"name-{ticker}",
        "sector": "Technology",
        "return_20d": 1.0,
        "relative_strength_20d": 0.1,
        "next_earnings_date": None,
        "price": 100.0,
        "price_source": "yfinance",
        "intraday_change_pct": None,
        "technical": {
            "price": 100.0,
            "short_term": {"score": 0.1, "label": "x"},
            "mid_term": {"score": 0.1, "label": "x"},
            "long_term": {"score": 0.1, "label": "x"},
            "dow_theory": {
                "daily": {"trend": "uptrend", "last_swings": swings, "confirmed_by_volume": True},
                "weekly": {"trend": "uptrend", "last_swings": [], "confirmed_by_volume": False},
            },
            "wyckoff_phase": {"phase": "markup", "since": None},
            "candlestick_pattern": {"pattern": None, "direction": 0, "bar_index": None},
            "fibonacci_position": {"levels": {0.0: 101.0, 0.5: 98.0, 0.618: 95.0},
                                   "price_zone": "0.500", "score": 0.5},
            "volume_profile": {"poc": 100.0, "value_area": (98.0, 102.0), "price_vs_poc": 0.0},
        },
        "macro_index": {"name": "sp500", "outlook": {}},
        "combined_technical_macro": {},
        "fundamentals_source": "Yahoo Finance News",
        "fundamentals_raw": [],
        "fundamentals_note": "note",
    }


def _make_frames():
    scan_df = pd.DataFrame({
        "ticker": ["AAA", "BBB"],
        "sector": ["Technology", "Technology"],
        "return_20d": [1.0, 2.0],
        "relative_strength_20d": [0.1, 0.2],
    })
    bullish = pd.DataFrame({
        "ticker": ["AAA", "BBB"],
        "avg_score": [0.9, 0.8],
        "entry_timeframe": [
            {"alignment": "aligned", "elliott_wave_context": "w1", "note": "ok"},
            {"alignment": "conflicting", "elliott_wave_context": "w2", "note": "careful"},
        ],
    })
    bearish = pd.DataFrame({"ticker": [], "avg_score": [], "entry_timeframe": []})
    name_map = {"AAA": "Alpha Co", "BBB": "Beta Co"}
    return scan_df, bullish, bearish, name_map


def test_build_market_block_threads_entry_timeframe_and_chart():
    scan_df, bullish, bearish, name_map = _make_frames()
    price_df = _fake_ohlcv_df()
    sentinel_chart = {"sentinel": True}

    with patch("generate_daily_watchlist.generate_report", side_effect=lambda t, **kw: _fake_report(t)), \
         patch("generate_daily_watchlist.save_report"), \
         patch("generate_daily_watchlist.get_daily", return_value=price_df) as mock_get_daily, \
         patch("generate_daily_watchlist.build_chart_data", return_value=sentinel_chart) as mock_chart:
        reports_out = {}
        entries = _build_market_block(scan_df, bullish, bearish, name_map, reports_out)

    assert len(entries["bullish"]) == 2
    assert entries["bearish"] == []

    by_ticker = {e["ticker"]: e for e in entries["bullish"]}
    assert by_ticker["AAA"]["entry_timeframe"] == {
        "alignment": "aligned", "elliott_wave_context": "w1", "note": "ok",
    }
    assert by_ticker["BBB"]["entry_timeframe"]["alignment"] == "conflicting"
    assert by_ticker["AAA"]["chart"] is sentinel_chart
    assert by_ticker["BBB"]["chart"] is sentinel_chart

    assert mock_get_daily.call_count == 2
    assert mock_chart.call_count == 2
    args, kwargs = mock_chart.call_args_list[0]
    report = _fake_report("AAA")
    tech = report["technical"]
    assert args[0] is price_df
    assert args[1] == tech["dow_theory"]["daily"]["last_swings"]
    assert args[2] == tech["fibonacci_position"]["levels"]
    assert args[3] == tech["candlestick_pattern"]
    assert args[4] == tech["wyckoff_phase"]

    assert set(reports_out.keys()) == {"AAA", "BBB"}


def test_build_market_block_feeds_real_build_chart_data():
    # build_chart_data is deliberately NOT mocked here: the other tests only prove the
    # arguments are forwarded, not that the real function can actually consume them.
    scan_df, bullish, bearish, name_map = _make_frames()
    price_df = _fake_ohlcv_df()

    with patch("generate_daily_watchlist.generate_report", side_effect=lambda t, **kw: _fake_report(t)), \
         patch("generate_daily_watchlist.save_report"), \
         patch("generate_daily_watchlist.get_daily", return_value=price_df):
        reports_out = {}
        entries = _build_market_block(scan_df, bullish, bearish, name_map, reports_out)

    assert len(entries["bullish"]) == 2
    for entry in entries["bullish"]:
        chart = entry["chart"]
        # A None chart here would mean the real function raised and was swallowed by the
        # chart-build try/except -- exactly the integration bug the mocks used to hide.
        assert chart is not None, f"real build_chart_data failed for {entry['ticker']}"
        assert set(chart.keys()) == {"ohlcv", "annotations"}
        assert len(chart["ohlcv"]) >= 1
        assert set(chart["ohlcv"][0].keys()) == {"date", "open", "high", "low", "close", "volume"}
        annotations = chart["annotations"]
        assert set(annotations.keys()) == {
            "swings", "fibonacci_levels", "wyckoff_zones", "candlestick_markers",
        }
        # The fixture's single in-window swing and its three fibonacci levels survive the trip.
        assert len(annotations["swings"]) == 1
        assert len(annotations["fibonacci_levels"]) == 3


def test_build_market_block_keeps_ticker_when_chart_build_fails():
    scan_df, bullish, bearish, name_map = _make_frames()
    price_df = _fake_ohlcv_df()

    def _chart_side_effect(*args, **kwargs):
        raise RuntimeError("boom")

    with patch("generate_daily_watchlist.generate_report", side_effect=lambda t, **kw: _fake_report(t)), \
         patch("generate_daily_watchlist.save_report"), \
         patch("generate_daily_watchlist.get_daily", return_value=price_df), \
         patch("generate_daily_watchlist.build_chart_data", side_effect=_chart_side_effect):
        reports_out = {}
        entries = _build_market_block(scan_df, bullish, bearish, name_map, reports_out)

    # Both candidates must still appear (the "show up to N" invariant), even though chart
    # building failed for all of them -- they must not be silently dropped.
    assert len(entries["bullish"]) == 2
    by_ticker = {e["ticker"]: e for e in entries["bullish"]}
    assert by_ticker["AAA"]["chart"] is None
    assert by_ticker["BBB"]["chart"] is None
    # entry_timeframe threading is unaffected by the chart failure.
    assert by_ticker["AAA"]["entry_timeframe"]["alignment"] == "aligned"

    # The report itself was generated successfully, so it must still land in reports_out --
    # a chart-build failure should not desync reports_out from the returned entries.
    assert set(reports_out.keys()) == {"AAA", "BBB"}


def test_build_market_block_partial_chart_failure_only_drops_chart_for_failing_ticker():
    scan_df, bullish, bearish, name_map = _make_frames()
    price_df = _fake_ohlcv_df()
    sentinel_chart = {"sentinel": True}

    def _chart_side_effect(*args, **kwargs):
        if _chart_side_effect.calls == 0:
            _chart_side_effect.calls += 1
            raise RuntimeError("boom")
        return sentinel_chart
    _chart_side_effect.calls = 0

    with patch("generate_daily_watchlist.generate_report", side_effect=lambda t, **kw: _fake_report(t)), \
         patch("generate_daily_watchlist.save_report"), \
         patch("generate_daily_watchlist.get_daily", return_value=price_df), \
         patch("generate_daily_watchlist.build_chart_data", side_effect=_chart_side_effect):
        reports_out = {}
        entries = _build_market_block(scan_df, bullish, bearish, name_map, reports_out)

    assert len(entries["bullish"]) == 2
    by_ticker = {e["ticker"]: e for e in entries["bullish"]}
    assert by_ticker["AAA"]["chart"] is None
    assert by_ticker["BBB"]["chart"] is sentinel_chart
    assert set(reports_out.keys()) == {"AAA", "BBB"}


def test_sanitize_recurses_into_tuples():
    # volume_profile's "value_area" is a tuple; without a tuple branch a NaN inside it
    # slipped past _sanitize and blew up json.dumps(allow_nan=False).
    result = _sanitize((float("nan"), 1.0))
    assert result == [None, 1.0]
    assert isinstance(result, list)


def test_sanitize_handles_nan_in_nested_volume_profile_tuple():
    profile = {"volume_profile": {"poc": 100.0, "value_area": (float("nan"), 102.0),
                                  "price_vs_poc": float("inf")}}
    cleaned = _sanitize(profile)
    assert cleaned["volume_profile"]["value_area"] == [None, 102.0]
    assert cleaned["volume_profile"]["price_vs_poc"] is None
    # The whole point: the sanitized structure is now strict-JSON serializable.
    assert json.dumps(cleaned, allow_nan=False)
