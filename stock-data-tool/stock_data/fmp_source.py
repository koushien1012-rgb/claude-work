import pandas as pd
import requests

from .common import REQUIRED_COLUMNS, get_api_key

_BASE_URL = "https://financialmodelingprep.com/api/v3"

_INTRADAY_INTERVALS = {"1min", "5min", "15min", "30min", "1hour", "4hour"}


def _request(path: str, params: dict | None = None) -> list | dict:
    params = params or {}
    params["apikey"] = get_api_key("FMP_API_KEY")
    resp = requests.get(f"{_BASE_URL}/{path}", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "Error Message" in data:
        raise ValueError(data["Error Message"])
    return data


def _to_dataframe(records: list, date_field: str = "date") -> pd.DataFrame:
    if not records:
        raise ValueError("No data returned.")
    df = pd.DataFrame(records)
    df.index = pd.to_datetime(df[date_field])
    df.index.name = "datetime"
    df = df.rename(columns=str.lower)
    df = df.sort_index()
    return df[REQUIRED_COLUMNS]


def get_daily(ticker: str, from_date: str | None = None, to_date: str | None = None) -> pd.DataFrame:
    params = {}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    data = _request(f"historical-price-full/{ticker}", params)
    records = data.get("historical", []) if isinstance(data, dict) else []
    return _to_dataframe(records)


def get_intraday(ticker: str, interval: str = "5min") -> pd.DataFrame:
    if interval not in _INTRADAY_INTERVALS:
        raise ValueError(
            f"Unsupported interval '{interval}' for FMP. "
            f"Choose one of: {sorted(_INTRADAY_INTERVALS)}"
        )
    data = _request(f"historical-chart/{interval}/{ticker}")
    return _to_dataframe(data)
