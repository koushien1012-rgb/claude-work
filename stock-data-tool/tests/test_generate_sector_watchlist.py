import json
import math
from unittest.mock import patch

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


def test_build_entry_fills_name_ja_for_us_ticker_with_known_translation():
    report = {
        "ticker": "SPCX", "name": "SpaceX", "price": 152.71, "price_source": "yfinance",
        "technical": {}, "fundamentals_source": "Yahoo Finance News", "fundamentals_raw": [],
    }
    entry = _build_entry("SPCX", report)
    assert entry["name_ja"] == "スペースX"


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


def _fake_report(ticker, name=None, **kwargs):
    if ticker == "FAIL_ME":
        raise RuntimeError("network error")
    return {
        "ticker": ticker, "name": name or ticker, "price": 100.0, "price_source": "yfinance",
        "technical": {"short_term": {"score": 0.1}, "mid_term": {"score": 0.1}, "long_term": {"score": 0.1}},
        "fundamentals_source": "TDnet", "fundamentals_raw": [],
    }


def test_save_and_load_snapshot_roundtrip(tmp_path):
    import generate_sector_watchlist as mod

    history_dir = tmp_path / "history"
    mod.save_snapshot(history_dir, "2026-09-20", {"SPCX": 0.1, "MU": 0.3})

    loaded = mod.load_previous_snapshot(history_dir, today="2026-09-21")
    assert loaded == {"SPCX": 0.1, "MU": 0.3}


def test_load_previous_snapshot_returns_none_when_no_history(tmp_path):
    import generate_sector_watchlist as mod

    assert mod.load_previous_snapshot(tmp_path / "does-not-exist", today="2026-09-21") is None


def test_load_previous_snapshot_picks_latest_before_today(tmp_path):
    import generate_sector_watchlist as mod

    history_dir = tmp_path / "history"
    mod.save_snapshot(history_dir, "2026-09-18", {"SPCX": 0.05})
    mod.save_snapshot(history_dir, "2026-09-20", {"SPCX": 0.10})
    # a same-day-or-future file (defensive: should not happen in practice) must never be picked
    mod.save_snapshot(history_dir, "2026-09-21", {"SPCX": 0.99})

    loaded = mod.load_previous_snapshot(history_dir, today="2026-09-21")
    assert loaded == {"SPCX": 0.10}  # 09-20, the latest strictly before today, not 09-21 itself


def test_main_writes_dashboard_json(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    small_sectors = {"宇宙": {"us": ["SPCX"], "jp": ["7011.T"]}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        mod.main()

    out_path = tmp_path / "dashboard" / "sector_watchlist_data.json"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "generated_at" in data
    assert data["sectors"][0]["name"] == "宇宙"
    assert data["sectors"][0]["us"][0]["ticker"] == "SPCX"
    assert data["sectors"][0]["jp"][0]["ticker"] == "7011.T"


def test_main_skips_failing_ticker_and_continues(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    small_sectors = {"宇宙": {"us": ["SPCX", "FAIL_ME"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        mod.main()

    data = json.loads((tmp_path / "dashboard" / "sector_watchlist_data.json").read_text(encoding="utf-8"))
    tickers = [e["ticker"] for e in data["sectors"][0]["us"]]
    assert tickers == ["SPCX"]  # FAIL_ME skipped, SPCX still present


def test_main_leaves_score_change_none_on_first_run(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    small_sectors = {"宇宙": {"us": ["SPCX"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        mod.main()  # no prior snapshot exists yet in this tmp_path

    data = json.loads((tmp_path / "dashboard" / "sector_watchlist_data.json").read_text(encoding="utf-8"))
    assert data["sectors"][0]["us"][0]["score_change"] is None


def test_main_computes_score_change_from_prior_snapshot(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()
    mod.save_snapshot(tmp_path / "output" / "sector_watchlist_history", "2026-09-20", {"SPCX": 0.0})

    small_sectors = {"宇宙": {"us": ["SPCX"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report), \
         patch.object(mod, "date") as mock_date:
        mock_date.today.return_value.isoformat.return_value = "2026-09-21"
        mod.main()

    data = json.loads((tmp_path / "dashboard" / "sector_watchlist_data.json").read_text(encoding="utf-8"))
    # _fake_report gives avg_score (0.1+0.1+0.1)/3 = 0.1; prior snapshot was 0.0 -> change is +0.1
    assert data["sectors"][0]["us"][0]["score_change"] == 0.1


def test_main_includes_fetched_and_expected_counts(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    small_sectors = {"宇宙": {"us": ["SPCX", "FAIL_ME"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        mod.main()

    data = json.loads((tmp_path / "dashboard" / "sector_watchlist_data.json").read_text(encoding="utf-8"))
    assert data["fetched"] == 1
    assert data["expected"] == 2


def test_main_aborts_and_preserves_existing_data_when_all_tickers_fail(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()
    out_path = tmp_path / "dashboard" / "sector_watchlist_data.json"
    out_path.write_text('{"generated_at": "yesterday", "sectors": []}', encoding="utf-8")

    small_sectors = {"宇宙": {"us": ["FAIL_ME"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        with pytest.raises(SystemExit):
            mod.main()

    # existing dashboard data must be left untouched, not overwritten with an empty payload
    assert out_path.read_text(encoding="utf-8") == '{"generated_at": "yesterday", "sectors": []}'
    # no snapshot should be recorded for a run that fetched nothing
    history_dir = tmp_path / "output" / "sector_watchlist_history"
    assert not history_dir.exists() or list(history_dir.glob("*.json")) == []


def test_main_skips_ticker_with_null_prior_snapshot_value(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()
    # simulates a prior snapshot value that was NaN and got sanitized to null
    mod.save_snapshot(tmp_path / "output" / "sector_watchlist_history", "2026-09-20", {"SPCX": None})

    small_sectors = {"宇宙": {"us": ["SPCX"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report), \
         patch.object(mod, "date") as mock_date:
        mock_date.today.return_value.isoformat.return_value = "2026-09-21"
        mod.main()  # must not raise despite a null value in the prior snapshot

    data = json.loads((tmp_path / "dashboard" / "sector_watchlist_data.json").read_text(encoding="utf-8"))
    assert data["sectors"][0]["us"][0]["score_change"] is None
