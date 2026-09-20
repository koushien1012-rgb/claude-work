import pandas as pd

from stock_data import get_daily

MACRO_TICKERS = {
    "nikkei225": "^N225",
    "dow": "^DJI",
    "sp500": "^GSPC",
    "usdjpy": "JPY=X",
    "gold": "GC=F",
    "crude_oil_wti": "CL=F",
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
}


def get_macro_daily(name: str, **kwargs) -> pd.DataFrame:
    ticker = MACRO_TICKERS.get(name, name)
    return get_daily(ticker, source="yfinance", **kwargs)


def get_macro_snapshot(period: str = "5d") -> pd.DataFrame:
    rows = []
    for name, ticker in MACRO_TICKERS.items():
        df = get_daily(ticker, source="yfinance", period=period)
        if df.empty:
            continue
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        change_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
        rows.append({
            "name": name,
            "ticker": ticker,
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "close": round(float(latest["close"]), 2),
            "change_pct": round(float(change_pct), 2),
        })
    return pd.DataFrame(rows)
