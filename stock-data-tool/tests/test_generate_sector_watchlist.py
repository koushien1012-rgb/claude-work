import math

import pytest

from generate_sector_watchlist import (
    SECTOR_TICKERS,
    _avg_score,
    _build_entry,
    _sanitize,
    build_sector_payload,
    dedupe_tickers,
)


def test_sector_tickers_covers_four_sectors_with_four_each():
    assert set(SECTOR_TICKERS.keys()) == {"宇宙", "防衛", "船舶", "メモリ半導体"}
    for sector, markets in SECTOR_TICKERS.items():
        assert len(markets["us"]) == 4, sector
        assert len(markets["jp"]) == 4, sector


def test_dedupe_tickers_removes_cross_sector_duplicates():
    sector_tickers = {
        "宇宙": {"us": ["SPCX"], "jp": ["7011.T"]},
        "防衛": {"us": ["LMT"], "jp": ["7011.T"]},
    }
    result = dedupe_tickers(sector_tickers)
    result_set = {(r["ticker"], r["market"]) for r in result}
    assert result_set == {("SPCX", "us"), ("7011.T", "jp"), ("LMT", "us")}
    assert len(result) == 3  # 7011.T counted once despite appearing in two sectors


def test_build_entry_shapes_report_for_dashboard():
    report = {
        "ticker": "7011.T", "name": "三菱重工業", "price": 3879.0, "price_source": "yfinance",
        "technical": {"short_term": {"score": 0.28, "label": "やや強気"}},
        "fundamentals_source": "TDnet",
        "fundamentals_raw": [{"title": "決算発表", "published_at": "2026-09-01"}],
    }
    entry = _build_entry("7011.T", report)
    assert entry["ticker"] == "7011.T"
    assert entry["name"] == "三菱重工業"
    assert entry["price"] == 3879.0
    assert entry["technical"] == report["technical"]
    assert entry["fundamentals_raw"] == report["fundamentals_raw"]
    assert entry["score_change"] is None  # default when no prior snapshot is passed


def test_build_entry_includes_score_change_when_provided():
    report = {
        "ticker": "MU", "name": "Micron", "price": 1015.8, "price_source": "yfinance",
        "technical": {}, "fundamentals_source": "Yahoo Finance News", "fundamentals_raw": [],
    }
    entry = _build_entry("MU", report, score_change=0.042)
    assert entry["score_change"] == 0.042


def test_avg_score_averages_the_three_terms():
    technical = {
        "short_term": {"score": 0.3}, "mid_term": {"score": 0.6}, "long_term": {"score": -0.3},
    }
    assert _avg_score(technical) == pytest.approx(0.2)


def test_build_sector_payload_duplicates_multi_sector_ticker():
    sector_tickers = {
        "宇宙": {"us": [], "jp": ["7011.T"]},
        "防衛": {"us": [], "jp": ["7011.T"]},
    }
    report = {
        "ticker": "7011.T", "name": "三菱重工業", "price": 3879.0, "price_source": "yfinance",
        "technical": {}, "fundamentals_source": "TDnet", "fundamentals_raw": [],
    }
    reports_by_ticker = {"7011.T": report}
    payload = build_sector_payload(sector_tickers, reports_by_ticker)
    assert len(payload) == 2
    assert payload[0]["name"] == "宇宙"
    assert payload[0]["jp"][0]["ticker"] == "7011.T"
    assert payload[1]["name"] == "防衛"
    assert payload[1]["jp"][0]["ticker"] == "7011.T"
    assert payload[0]["us"] == []


def test_build_sector_payload_passes_score_change_through():
    sector_tickers = {"宇宙": {"us": ["SPCX"], "jp": []}}
    report = {
        "ticker": "SPCX", "name": "SpaceX", "price": 152.71, "price_source": "yfinance",
        "technical": {}, "fundamentals_source": "Yahoo Finance News", "fundamentals_raw": [],
    }
    payload = build_sector_payload(sector_tickers, {"SPCX": report}, score_changes={"SPCX": -0.05})
    assert payload[0]["us"][0]["score_change"] == -0.05


def test_build_sector_payload_skips_ticker_missing_from_reports():
    # a ticker whose report fetch failed (Task 2's error handling) is simply
    # absent from reports_by_ticker; the payload must omit it, not crash
    sector_tickers = {"宇宙": {"us": ["SPCX"], "jp": []}}
    payload = build_sector_payload(sector_tickers, reports_by_ticker={})
    assert payload[0]["us"] == []


def test_sanitize_converts_nan_and_inf_to_none():
    assert _sanitize(float("nan")) is None
    assert _sanitize(float("inf")) is None
    assert _sanitize({"a": [1.0, float("nan")], "b": (2.0, float("inf"))}) == {"a": [1.0, None], "b": [2.0, None]}
