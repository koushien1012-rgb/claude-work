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

    result = refine_candidates(candidate_df, daily_trends, n=2, ascending=False, fetch_intraday=fetch)
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

    result = refine_candidates(candidate_df, daily_trends, n=3, ascending=False, fetch_intraday=fetch)
    assert len(result) == 3  # processing continues past the failed ticker instead of raising
    fail_row = result[result["ticker"] == "FAIL"].iloc[0]
    assert fail_row["entry_timeframe"]["alignment"] == "unknown"
    ok_row = result[result["ticker"] == "OK1"].iloc[0]
    assert ok_row["entry_timeframe"]["alignment"] == "aligned"
