import json
from datetime import date
from pathlib import Path

import pandas as pd

from stock_data import get_daily

HISTORY_DIR = Path("output/watchlist/history")
MIN_AGE_DAYS = 5


def load_snapshots() -> list[dict]:
    snapshots = []
    for path in sorted(HISTORY_DIR.glob("*.json")):
        try:
            snapshots.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return snapshots


def evaluate():
    snapshots = load_snapshots()
    today = date.today()
    eligible = [s for s in snapshots if (today - date.fromisoformat(s["date"])).days >= MIN_AGE_DAYS]
    if not eligible:
        print(f"評価可能なデータがまだありません（{MIN_AGE_DAYS}日以上前のスナップショットが必要です）。")
        print(f"現在保存されているスナップショット数: {len(snapshots)}")
        return

    price_cache: dict = {}
    rows = []
    for snap in eligible:
        snap_date = date.fromisoformat(snap["date"])
        for row in snap["rows"]:
            ticker = row["ticker"]
            if ticker not in price_cache:
                try:
                    price_cache[ticker] = get_daily(ticker, source="yfinance", period="6mo")
                except Exception:
                    price_cache[ticker] = None
            df = price_cache[ticker]
            if df is None or df.empty:
                continue
            after = df[df.index.date > snap_date]
            if after.empty or not row.get("price") or row.get("avg_score") is None:
                continue
            future_price = after.iloc[0]["close"]
            realized_return = (future_price - row["price"]) / row["price"] * 100
            rows.append({
                "date": snap["date"],
                "ticker": ticker,
                "avg_score": row["avg_score"],
                "realized_return_pct": round(realized_return, 2),
                "predicted_direction": "bullish" if row["avg_score"] > 0 else "bearish",
                "realized_direction": "up" if realized_return > 0 else "down",
            })

    if not rows:
        print("評価対象の銘柄データが取得できませんでした。")
        return

    result_df = pd.DataFrame(rows)
    result_df["hit"] = (
        ((result_df["predicted_direction"] == "bullish") & (result_df["realized_direction"] == "up"))
        | ((result_df["predicted_direction"] == "bearish") & (result_df["realized_direction"] == "down"))
    )
    print(f"評価件数: {len(result_df)}")
    print(f"総合的中率: {result_df['hit'].mean() * 100:.1f}%")
    print()
    print("方向別的中率:")
    print((result_df.groupby("predicted_direction")["hit"].mean() * 100).round(1))

    out_path = HISTORY_DIR.parent / "backtest_result.csv"
    result_df.to_csv(out_path, index=False)
    print(f"\n詳細をCSVに保存しました: {out_path}")


if __name__ == "__main__":
    evaluate()
