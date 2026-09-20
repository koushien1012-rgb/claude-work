from unittest.mock import patch

import numpy as np
import pandas as pd

from screener.intraday_refine import refine_candidate, refine_candidates


def _fake_hourly_uptrend(ticker, interval="1h", period="60d"):
    n = 24 * 30  # 30 days of hourly bars
    t = np.arange(n)
    closes = 100 + 0.05 * t + 2 * np.sin(2 * np.pi * t / 24)
    dates = pd.date_range("2024-06-01", periods=n, freq="h")
    return pd.DataFrame({
        "open": closes, "high": closes + 0.5, "low": closes - 0.5, "close": closes,
        "volume": np.linspace(100, 300, n),
    }, index=dates)


def _fake_hourly_failure(ticker, interval="1h", period="60d"):
    raise RuntimeError("no data")


def test_refine_candidate_reports_aligned_when_trends_match():
    result = refine_candidate("TESTX", daily_trend="up", fetch_intraday=_fake_hourly_uptrend)
    assert result["alignment"] == "aligned"
    assert "波" in result["elliott_wave_context"]


def test_refine_candidate_context_does_not_fabricate_a_wave_number():
    # Elliott wave counting is not actually performed; the context must describe the
    # detected swings instead of asserting a "第N波" count.
    result = refine_candidate("TESTX", daily_trend="up", fetch_intraday=_fake_hourly_uptrend)
    context = result["elliott_wave_context"]
    assert "第" not in context
    assert "波目" not in context
    assert "スイング" in context
    assert "波動カウントは未実施" in context


def test_refine_candidate_note_does_not_claim_weekly_alignment():
    # Only daily vs 4h is compared in this function -- the weekly trend is never passed in.
    aligned = refine_candidate("TESTX", daily_trend="up", fetch_intraday=_fake_hourly_uptrend)
    assert aligned["note"] == "日足・4時間足のトレンドが一致しています"
    assert "週足" not in aligned["note"]

    conflicting = refine_candidate("TESTX", daily_trend="down", fetch_intraday=_fake_hourly_uptrend)
    assert "週足" not in conflicting["note"]


def test_refine_candidate_reports_conflicting_when_trends_differ():
    result = refine_candidate("TESTX", daily_trend="down", fetch_intraday=_fake_hourly_uptrend)
    assert result["alignment"] == "conflicting"


def test_refine_candidate_handles_fetch_failure_gracefully():
    result = refine_candidate("TESTX", daily_trend="up", fetch_intraday=_fake_hourly_failure)
    assert result["alignment"] == "unknown"


def test_refine_candidates_ranks_aligned_first_and_truncates():
    candidate_df = pd.DataFrame({
        "ticker": ["A", "B", "C"],
        "avg_score": [0.9, 0.8, 0.7],
    })
    daily_trends = {"A": "down", "B": "up", "C": "up"}  # A will conflict, B and C align

    def fetch(ticker, interval="1h", period="60d"):
        if ticker == "A":
            return _fake_hourly_uptrend(ticker)  # uptrend hourly, but daily says "down" -> conflicting
        return _fake_hourly_uptrend(ticker)  # aligned with "up" daily trend

    result = refine_candidates(candidate_df, daily_trends, n=2, ascending=False,
                               fetch_intraday=fetch, pause=0)
    assert len(result) == 2
    assert "A" not in result["ticker"].to_list()  # conflicting candidate pushed out by aligned ones


def test_refine_candidates_skips_failed_fetch_and_keeps_others():
    candidate_df = pd.DataFrame({
        "ticker": ["FAIL", "OK1", "OK2"],
        "avg_score": [0.95, 0.8, 0.7],
    })
    daily_trends = {"FAIL": "up", "OK1": "up", "OK2": "up"}

    def fetch(ticker, interval="1h", period="60d"):
        if ticker == "FAIL":
            raise RuntimeError("delisted or renamed ticker")
        return _fake_hourly_uptrend(ticker)

    result = refine_candidates(candidate_df, daily_trends, n=3, ascending=False,
                               fetch_intraday=fetch, pause=0)
    assert len(result) == 3  # processing continues past the failed ticker instead of raising
    fail_row = result[result["ticker"] == "FAIL"].iloc[0]
    assert fail_row["entry_timeframe"]["alignment"] == "unknown"
    ok_row = result[result["ticker"] == "OK1"].iloc[0]
    assert ok_row["entry_timeframe"]["alignment"] == "aligned"


def test_refine_candidates_logs_failure_and_summary(capsys):
    candidate_df = pd.DataFrame({
        "ticker": ["FAIL", "OK1", "CONFLICT"],
        "avg_score": [0.95, 0.8, 0.7],
    })
    daily_trends = {"FAIL": "up", "OK1": "up", "CONFLICT": "down"}

    def fetch(ticker, interval="1h", period="60d"):
        if ticker == "FAIL":
            raise RuntimeError("delisted or renamed ticker")
        return _fake_hourly_uptrend(ticker)

    refine_candidates(candidate_df, daily_trends, n=3, ascending=False,
                      fetch_intraday=fetch, pause=0)
    out = capsys.readouterr().out
    # The swallowed fetch failure is now surfaced instead of silently degrading.
    assert "stage-2 refine failed for FAIL" in out
    assert "delisted or renamed ticker" in out
    assert "stage-2 refine: 1 aligned, 1 conflicting, 1 unavailable (of 3)" in out


def test_refine_candidates_sleeps_between_candidates():
    candidate_df = pd.DataFrame({"ticker": ["A", "B", "C"], "avg_score": [0.9, 0.8, 0.7]})
    daily_trends = {"A": "up", "B": "up", "C": "up"}
    calls = []

    with patch("screener.intraday_refine.time.sleep", side_effect=calls.append):
        refine_candidates(candidate_df, daily_trends, n=3, ascending=False,
                          fetch_intraday=_fake_hourly_uptrend)

    # One throttle pause per candidate, using the default pause.
    assert calls == [0.3, 0.3, 0.3]


def test_refine_candidates_returns_empty_without_raising_on_empty_pool():
    # pd.DataFrame([]) from an empty enrich loop has no columns at all, so the old code
    # raised KeyError: 'entry_timeframe' on a zero-row pool.
    candidate_df = pd.DataFrame({"ticker": [], "avg_score": []})
    result = refine_candidates(candidate_df, {}, n=10, ascending=False,
                               fetch_intraday=_fake_hourly_failure, pause=0)
    assert result.empty
    assert len(result) == 0
    # Column schema still matches what downstream consumers expect.
    assert "ticker" in result.columns
    assert "entry_timeframe" in result.columns
    assert list(result["ticker"]) == []
