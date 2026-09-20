import json
from pathlib import Path

from analysis import compute_indicators, outlook
from stock_data import get_daily

_STATE_PATH = Path("output/watchlist/watchlist_state.json")


def _load_state() -> dict:
    if _STATE_PATH.exists():
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _cross_sign(details: dict, key: str) -> int | None:
    value = details.get(key)
    if value is None:
        return None
    return 1 if value > 0 else (-1 if value < 0 else 0)


def check_watchlist_alerts(tickers: list[str], name_map: dict) -> list[dict]:
    if not tickers:
        return []
    prev_state = _load_state()
    new_state = {}
    alerts = []

    for ticker in tickers:
        try:
            df = get_daily(ticker, source="yfinance", period="1y")
            result = outlook(compute_indicators(df), df)
        except Exception as exc:
            alerts.append({"ticker": ticker, "name": name_map.get(ticker, ""),
                            "message": f"データ取得に失敗しました: {exc}"})
            continue

        mid_cross = _cross_sign(result["mid_term"]["details"], "sma25_vs_sma75")
        long_cross = _cross_sign(result["long_term"]["details"], "sma75_vs_sma200")
        current = {
            "short_label": result["short_term"]["label"],
            "mid_label": result["mid_term"]["label"],
            "long_label": result["long_term"]["label"],
            "mid_cross": mid_cross,
            "long_cross": long_cross,
        }
        new_state[ticker] = current

        prev = prev_state.get(ticker)
        name = name_map.get(ticker, "")
        if prev is None:
            new_state[ticker] = current
            continue

        if prev.get("mid_cross") is not None and mid_cross is not None and prev["mid_cross"] != mid_cross:
            kind = "ゴールデンクロス（25日線が75日線を上抜け）" if mid_cross > 0 else "デッドクロス（25日線が75日線を割れ）"
            alerts.append({"ticker": ticker, "name": name, "message": f"中期: {kind}が発生しました"})

        if prev.get("long_cross") is not None and long_cross is not None and prev["long_cross"] != long_cross:
            kind = "ゴールデンクロス（75日線が200日線を上抜け）" if long_cross > 0 else "デッドクロス（75日線が200日線を割れ）"
            alerts.append({"ticker": ticker, "name": name, "message": f"長期: {kind}が発生しました"})

        for term_key, term_label in (("short_label", "短期"), ("mid_label", "中期"), ("long_label", "長期")):
            if prev.get(term_key) != current[term_key]:
                alerts.append({
                    "ticker": ticker, "name": name,
                    "message": f"{term_label}見通しが「{prev.get(term_key)}」→「{current[term_key]}」に変化しました",
                })

    _save_state(new_state)
    return alerts
