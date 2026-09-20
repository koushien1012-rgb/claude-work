import pandas as pd
import requests

from .common import REQUIRED_COLUMNS, get_api_key

_BASE_URL = "https://www.alphavantage.co/query"

_INTRADAY_INTERVALS = {"1min", "5min", "15min", "30min", "60min"}

_COLUMN_MAP = {
    "1. open": "open",
    "2. high": "high",
    "3. low": "low",
    "4. close": "close",
    "5. volume": "volume",
}


def _request(params: dict) -> dict:
    params["apikey"] = get_api_key("ALPHAVANTAGE_API_KEY")
    resp = requests.get(_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "Error Message" in data:
        raise ValueError(data["Error Message"])
    if "Note" in data:
        raise RuntimeError(data["Note"])
    return data


def _to_dataframe(data: dict, series_key: str) -> pd.DataFrame:
    series = data.get(series_key)
    if not series:
        raise ValueError(f"No data returned (missing key '{series_key}').")
    df = pd.DataFrame.from_dict(series, orient="index")
    df = df.rename(columns=_COLUMN_MAP).astype(float)
    df.index = pd.to_datetime(df.index)
    df.index.name = "datetime"
    df = df.sort_index()
    return df[REQUIRED_COLUMNS]


def get_daily(ticker: str, outputsize: str = "compact") -> pd.DataFrame:
    data = _request({
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": outputsize,
    })
    return _to_dataframe(data, "Time Series (Daily)")


def get_intraday(ticker: str, interval: str = "5min", outputsize: str = "compact") -> pd.DataFrame:
    if interval not in _INTRADAY_INTERVALS:
        raise ValueError(
            f"Unsupported interval '{interval}' for Alpha Vantage. "
            f"Choose one of: {sorted(_INTRADAY_INTERVALS)}"
        )
    data = _request({
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": interval,
        "outputsize": outputsize,
    })
    return _to_dataframe(data, f"Time Series ({interval})")
