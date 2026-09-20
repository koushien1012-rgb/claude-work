import pandas as pd

from analysis.dow_theory import analyze as dow_analyze
from stock_data import get_intraday


def _resample_4h(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("4h").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
    }).dropna()


def _elliott_wave_context(swings: list[dict]) -> str:
    """Rough, non-predictive wave count label based on recent swing count. Context only, never scored."""
    count = len(swings)
    wave = min(max(count % 5, 1), 5)
    return f"直近スイングから推定 第{wave}波目（目安・参考情報）"


def refine_candidate(ticker: str, daily_trend: str, fetch_intraday=get_intraday) -> dict:
    try:
        hourly = fetch_intraday(ticker, interval="1h", period="60d")
    except Exception:
        return {"alignment": "unknown", "elliott_wave_context": "データ取得失敗", "note": "1時間足データを取得できませんでした"}

    if hourly is None or hourly.empty or len(hourly) < 30:
        return {"alignment": "unknown", "elliott_wave_context": "データ不足", "note": "1時間足データが不足しています"}

    four_hour = _resample_4h(hourly)
    result = dow_analyze(four_hour, window=3)
    alignment = "aligned" if result["trend"] == daily_trend else "conflicting"
    context = _elliott_wave_context(result["last_swings"])
    note = ("週足・日足・4時間足のトレンドが一致しています" if alignment == "aligned"
            else "4時間足トレンドが日足と逆行しています。エントリータイミングに注意してください")
    return {"alignment": alignment, "elliott_wave_context": context, "note": note}


def refine_candidates(candidate_df: pd.DataFrame, daily_trends: dict, n: int = 10,
                       ascending: bool = False, fetch_intraday=get_intraday) -> pd.DataFrame:
    """candidate_df must already be sorted by avg_score (stage-1 ranking)."""
    enriched = []
    for _, row in candidate_df.iterrows():
        ticker = row["ticker"]
        entry_info = refine_candidate(ticker, daily_trends.get(ticker, "sideways"), fetch_intraday=fetch_intraday)
        record = row.to_dict()
        record["entry_timeframe"] = entry_info
        enriched.append(record)

    result_df = pd.DataFrame(enriched)
    result_df["_alignment_bonus"] = result_df["entry_timeframe"].apply(
        lambda info: 1 if info.get("alignment") == "aligned" else 0
    )
    result_df = result_df.sort_values(["_alignment_bonus", "avg_score"], ascending=[False, ascending]).head(n)
    return result_df.drop(columns=["_alignment_bonus"]).reset_index(drop=True)
