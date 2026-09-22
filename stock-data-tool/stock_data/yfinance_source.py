import pandas as pd
import yfinance as yf

from .common import REQUIRED_COLUMNS

_INTRADAY_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    df.index.name = "datetime"
    return df[REQUIRED_COLUMNS]


def get_daily(ticker: str, start: str | None = None, end: str | None = None,
              period: str | None = None) -> pd.DataFrame:
    if start or end:
        df = yf.Ticker(ticker).history(interval="1d", start=start, end=end)
    else:
        df = yf.Ticker(ticker).history(interval="1d", period=period or "1y")
    return _normalize(df)


def get_intraday(ticker: str, interval: str = "5m", period: str = "5d") -> pd.DataFrame:
    if interval not in _INTRADAY_INTERVALS:
        raise ValueError(
            f"Unsupported interval '{interval}' for yfinance. "
            f"Choose one of: {sorted(_INTRADAY_INTERVALS)}"
        )
    # yfinance limits intraday history: 1m -> 7d max, others -> 60d max
    df = yf.Ticker(ticker).history(interval=interval, period=period)
    return _normalize(df)


def get_next_earnings_date(ticker: str) -> str | None:
    try:
        cal = yf.Ticker(ticker).calendar
    except Exception:
        return None
    if not isinstance(cal, dict):
        return None
    dates = cal.get("Earnings Date")
    if not dates:
        return None
    date = dates[0] if isinstance(dates, list) else dates
    return date.isoformat() if hasattr(date, "isoformat") else str(date)


def get_business_summary_en(ticker: str) -> str | None:
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return None
    summary = info.get("longBusinessSummary") if isinstance(info, dict) else None
    return summary.strip() if summary else None
