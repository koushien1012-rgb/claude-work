import time

import pandas as pd
import yfinance as yf

from analysis import compute_indicators, outlook


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    return df[["open", "high", "low", "close", "volume"]].dropna()


def _return_pct(close: pd.Series, window: int) -> float | None:
    if len(close) <= window:
        return None
    return round((close.iloc[-1] / close.iloc[-1 - window] - 1) * 100, 2)


def scan_universe(tickers: list[str], name_map: dict | None = None, sector_map: dict | None = None,
                   period: str = "1y", batch_size: int = 50, pause: float = 1.0) -> pd.DataFrame:
    name_map = name_map or {}
    sector_map = sector_map or {}
    rows = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(batch, period=period, group_by="ticker", threads=True,
                                progress=False, auto_adjust=False)
        except Exception:
            continue
        for ticker in batch:
            try:
                df = data[ticker] if len(batch) > 1 else data
                df = _normalize_ohlcv(df.dropna(how="all"))
                if len(df) < 60:
                    continue
                result = outlook(compute_indicators(df), df)
                scores = [result["short_term"]["score"], result["mid_term"]["score"], result["long_term"]["score"]]
                rows.append({
                    "ticker": ticker,
                    "name": name_map.get(ticker, ""),
                    "sector": sector_map.get(ticker, ""),
                    "price": result["price"],
                    "short_score": result["short_term"]["score"],
                    "mid_score": result["mid_term"]["score"],
                    "long_score": result["long_term"]["score"],
                    "avg_score": round(sum(scores) / len(scores), 3),
                    "return_20d": _return_pct(df["close"], 20),
                })
            except Exception:
                continue
        if i + batch_size < len(tickers):
            time.sleep(pause)

    scan_df = pd.DataFrame(rows)
    if not scan_df.empty and "sector" in scan_df:
        sector_mean = scan_df.groupby("sector")["return_20d"].transform("mean")
        scan_df["relative_strength_20d"] = (scan_df["return_20d"] - sector_mean).round(2)
    return scan_df


def top_signals(scan_df: pd.DataFrame, n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    bullish = scan_df.sort_values("avg_score", ascending=False).head(n).reset_index(drop=True)
    bearish = scan_df.sort_values("avg_score", ascending=True).head(n).reset_index(drop=True)
    return bullish, bearish
