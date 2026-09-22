from pathlib import Path

import pandas as pd

from . import alphavantage_source, fmp_source, moomoo_source, yfinance_source

_SOURCES = {
    "yfinance": yfinance_source,
    "alphavantage": alphavantage_source,
    "fmp": fmp_source,
}

# canonical interval -> per-source interval string
_INTERVAL_MAP = {
    "yfinance": {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m"},
    "alphavantage": {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "60min"},
    "fmp": {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "1hour"},
}


def get_daily(ticker: str, source: str = "yfinance", **kwargs) -> pd.DataFrame:
    module = _SOURCES[source]
    return module.get_daily(ticker, **kwargs)


def get_intraday(ticker: str, source: str = "yfinance", interval: str = "5m", **kwargs) -> pd.DataFrame:
    module = _SOURCES[source]
    native_interval = _INTERVAL_MAP[source].get(interval, interval)
    return module.get_intraday(ticker, interval=native_interval, **kwargs)


def save_csv(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return path


def get_next_earnings_date(ticker: str) -> str | None:
    return yfinance_source.get_next_earnings_date(ticker)


def get_business_summary_en(ticker: str) -> str | None:
    return yfinance_source.get_business_summary_en(ticker)


def get_us_realtime_snapshot(tickers: list[str]) -> dict:
    return moomoo_source.get_us_realtime_snapshot(tickers)


__all__ = [
    "get_daily", "get_intraday", "save_csv", "get_next_earnings_date",
    "get_business_summary_en", "get_us_realtime_snapshot",
]
