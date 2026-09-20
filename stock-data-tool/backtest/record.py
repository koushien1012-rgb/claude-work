import json
from pathlib import Path

DASHBOARD_PATH = Path("output/watchlist/dashboard_data.json")
HISTORY_PATH = Path("output/watchlist/history/predictions.jsonl")

_TERMS = ("short_term", "mid_term", "long_term")
_JUDGMENT_TERMS = ("short", "mid", "long", "fundamental")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def record_snapshot(dashboard_path: Path = DASHBOARD_PATH, history_path: Path = HISTORY_PATH) -> int:
    """dashboard_data.json の当日分の予想(銘柄ごとの combined スコアと claude_judgment)を
    履歴ログ(predictions.jsonl)に追記する。同じ日・銘柄・市場・区分の重複は追記しない。
    """
    dashboard_path = Path(dashboard_path)
    history_path = Path(history_path)

    data = json.loads(dashboard_path.read_text(encoding="utf-8"))
    entry_date = data["generated_at"][:10]
    run_type = data.get("run_type")

    existing_keys = {
        (rec["entry_date"], rec["ticker"], rec["market"], rec["side"])
        for rec in _load_jsonl(history_path)
    }

    new_records = []
    for market in ("jp", "us"):
        for side in ("bullish", "bearish"):
            for item in data.get("markets", {}).get(market, {}).get(side, []):
                key = (entry_date, item["ticker"], market, side)
                if key in existing_keys:
                    continue

                combined = item.get("combined") or {}
                judgment = item.get("claude_judgment")

                record = {
                    "entry_date": entry_date,
                    "run_type": run_type,
                    "market": market,
                    "side": side,
                    "ticker": item["ticker"],
                    "name": item.get("name"),
                    "name_ja": item.get("name_ja"),
                    "entry_price": item.get("price"),
                    "combined": {
                        term: {
                            "score": (combined.get(term) or {}).get("score"),
                            "label": (combined.get(term) or {}).get("label"),
                        }
                        for term in _TERMS
                    },
                    "claude_judgment": (
                        {
                            term: {"label": (judgment.get(term) or {}).get("label")}
                            for term in _JUDGMENT_TERMS
                        }
                        if judgment
                        else None
                    ),
                }
                new_records.append(record)
                existing_keys.add(key)

    if new_records:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as f:
            for rec in new_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return len(new_records)


if __name__ == "__main__":
    n = record_snapshot()
    print(f"recorded {n} new predictions -> {HISTORY_PATH}")
