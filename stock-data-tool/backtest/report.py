import json
from pathlib import Path

from .config import HORIZON_LABEL_JA

RESULT_PATH = Path("output/watchlist/history/results.jsonl")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _hit_rate(rows: list[dict], hit_key: str):
    hits = [r[hit_key] for r in rows if r[hit_key] is not None]
    if not hits:
        return None, 0
    return sum(hits) / len(hits) * 100, len(hits)


def build_report(result_path: Path = RESULT_PATH) -> str:
    results = _load_jsonl(result_path)
    lines = ["=== バックテスト結果サマリー ==="]

    if not results:
        lines.append("まだ評価済みの結果がありません（十分な営業日が経過するまでお待ちください）")
        text = "\n".join(lines)
        print(text)
        return text

    for horizon, label in HORIZON_LABEL_JA.items():
        rows = [r for r in results if r["horizon"] == horizon]
        if not rows:
            continue
        lines.append(f"\n[{label}] 評価件数: {len(rows)}")

        rate, n = _hit_rate(rows, "technical_hit")
        lines.append(
            f"  テクニカルスコアの的中率: {rate:.1f}% ({n}件、中立除く)" if rate is not None
            else "  テクニカルスコアの的中率: データなし"
        )

        rate, n = _hit_rate(rows, "judgment_hit")
        lines.append(
            f"  Claude総合判断の的中率: {rate:.1f}% ({n}件、中立除く)" if rate is not None
            else "  Claude総合判断の的中率: データなし"
        )

        bull = [r["return_pct"] for r in rows if r["side"] == "bullish"]
        bear = [r["return_pct"] for r in rows if r["side"] == "bearish"]
        if bull:
            lines.append(f"  強気選出銘柄の平均リターン: {sum(bull) / len(bull):+.2f}% ({len(bull)}件)")
        if bear:
            lines.append(f"  弱気選出銘柄の平均リターン: {sum(bear) / len(bear):+.2f}% ({len(bear)}件)")

    text = "\n".join(lines)
    print(text)
    return text


if __name__ == "__main__":
    build_report()
