import json
from datetime import date, datetime
from pathlib import Path

import stock_data

from .config import HORIZONS_TRADING_DAYS, LABEL_LEAN

PRED_PATH = Path("output/watchlist/history/predictions.jsonl")
RESULT_PATH = Path("output/watchlist/history/results.jsonl")

_TERM_KEY = {"short": "short_term", "mid": "mid_term", "long": "long_term"}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _entry_index(df, entry_date_str: str):
    """entry_date 以前で最も新しい取引日の行インデックスを返す。"""
    entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
    idx = None
    for i, ts in enumerate(df.index):
        d = ts.date() if hasattr(ts, "date") else ts
        if d <= entry_date:
            idx = i
        else:
            break
    return idx


def _hit(label: str | None, return_pct: float):
    if not label:
        return None
    lean = LABEL_LEAN.get(label)
    if not lean:  # None または 0(中立) は的中判定の対象外
        return None
    return bool((lean > 0 and return_pct > 0) or (lean < 0 and return_pct < 0))


def evaluate_pending(pred_path: Path = PRED_PATH, result_path: Path = RESULT_PATH) -> int:
    """十分な営業日数が経過した予想について、実際の株価と照合し results.jsonl に追記する。"""
    predictions = _load_jsonl(pred_path)
    if not predictions:
        print("予想の記録がまだありません（backtest/record.py を先に実行してください）")
        return 0

    already_done = {
        (rec["entry_date"], rec["ticker"], rec["market"], rec["side"], rec["horizon"])
        for rec in _load_jsonl(result_path)
    }

    pending_by_ticker: dict[str, list[tuple[dict, str]]] = {}
    for rec in predictions:
        for horizon in HORIZONS_TRADING_DAYS:
            key = (rec["entry_date"], rec["ticker"], rec["market"], rec["side"], horizon)
            if key in already_done:
                continue
            pending_by_ticker.setdefault(rec["ticker"], []).append((rec, horizon))

    if not pending_by_ticker:
        print("評価待ちの予想はありません（既にすべて評価済みです）")
        return 0

    new_results = []
    for ticker, items in pending_by_ticker.items():
        try:
            df = stock_data.get_daily(ticker, period="2y")
        except Exception as exc:
            print(f"skip {ticker}: 価格取得に失敗 ({exc})")
            continue
        if df is None or df.empty:
            continue

        for rec, horizon in items:
            idx = _entry_index(df, rec["entry_date"])
            if idx is None:
                continue
            offset = HORIZONS_TRADING_DAYS[horizon]
            target_idx = idx + offset
            if target_idx >= len(df):
                continue  # まだ十分な営業日が経過していない

            entry_price = rec.get("entry_price")
            if not entry_price:
                continue
            actual_price = float(df["close"].iloc[target_idx])
            return_pct = round((actual_price / entry_price - 1.0) * 100, 2)

            term_key = _TERM_KEY[horizon]
            tech_label = (rec.get("combined") or {}).get(term_key, {}).get("label")
            judgment = rec.get("claude_judgment") or {}
            judg_label = (judgment.get(horizon) or {}).get("label")

            new_results.append({
                "entry_date": rec["entry_date"],
                "evaluated_at": date.today().isoformat(),
                "market": rec["market"],
                "side": rec["side"],
                "ticker": ticker,
                "name_ja": rec.get("name_ja") or rec.get("name"),
                "horizon": horizon,
                "horizon_trading_days": offset,
                "entry_price": entry_price,
                "actual_price": actual_price,
                "return_pct": return_pct,
                "technical_label": tech_label,
                "technical_hit": _hit(tech_label, return_pct),
                "judgment_label": judg_label,
                "judgment_hit": _hit(judg_label, return_pct),
            })

    if new_results:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with result_path.open("a", encoding="utf-8") as f:
            for r in new_results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(new_results)} 件を新たに評価しました -> {result_path}")
    return len(new_results)


if __name__ == "__main__":
    evaluate_pending()
