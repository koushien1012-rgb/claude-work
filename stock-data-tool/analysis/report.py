from pathlib import Path

from macro import get_macro_daily
from news import get_tdnet_disclosures, get_yfinance_news
from stock_data import get_daily, get_next_earnings_date

from .signals import label_for_score, outlook
from .technical import compute_indicators

_JP_INDEX = "nikkei225"
_US_INDEX = "sp500"
_TERMS = (("short_term", "短期"), ("mid_term", "中期"), ("long_term", "長期"))


def _is_japanese_ticker(ticker: str) -> bool:
    return ticker.upper().endswith(".T")


def _blend(stock_term: dict, macro_term: dict, stock_weight: float = 0.7) -> dict:
    score = round(stock_weight * stock_term["score"] + (1 - stock_weight) * macro_term["score"], 3)
    return {"score": score, "label": label_for_score(score)}


def generate_report(ticker: str, news_limit: int = 8, name: str | None = None,
                     sector: str | None = None, return_20d: float | None = None,
                     relative_strength_20d: float | None = None,
                     realtime: dict | None = None) -> dict:
    df = get_daily(ticker, source="yfinance", period="2y")
    indicators = compute_indicators(df)
    stock_outlook = outlook(indicators, df)

    price = stock_outlook["price"]
    price_source = "yfinance"
    intraday_change_pct = None
    if realtime and realtime.get("price"):
        price = realtime["price"]
        price_source = "moomoo_realtime"
        intraday_change_pct = realtime.get("change_pct")

    index_name = _JP_INDEX if _is_japanese_ticker(ticker) else _US_INDEX
    index_df = get_macro_daily(index_name, period="2y")
    index_outlook = outlook(compute_indicators(index_df), index_df)

    combined = {term: _blend(stock_outlook[term], index_outlook[term]) for term, _ in _TERMS}

    if _is_japanese_ticker(ticker):
        fundamentals = get_tdnet_disclosures(code=ticker.split(".")[0], limit=news_limit)
        fundamentals_source = "TDnet"
    else:
        fundamentals = get_yfinance_news(ticker, limit=news_limit)
        fundamentals_source = "Yahoo Finance News"

    return {
        "ticker": ticker,
        "name": name,
        "sector": sector,
        "return_20d": return_20d,
        "relative_strength_20d": relative_strength_20d,
        "next_earnings_date": get_next_earnings_date(ticker),
        "price": price,
        "price_source": price_source,
        "intraday_change_pct": intraday_change_pct,
        "technical": {
            **stock_outlook,
            "dow_theory": {"daily": indicators["dow_daily"], "weekly": indicators["dow_weekly"]},
            "wyckoff_phase": indicators["wyckoff"],
            "candlestick_pattern": indicators["candlestick"],
            "fibonacci_position": indicators["fibonacci"],
            "volume_profile": indicators["volume_profile"],
        },
        "macro_index": {"name": index_name, "outlook": index_outlook},
        "combined_technical_macro": combined,
        "fundamentals_source": fundamentals_source,
        "fundamentals_raw": fundamentals,
        "fundamentals_note": (
            "自動スコアリングは未実施です。上記の見出し・開示内容を確認し、"
            "必要に応じてこの内容をClaudeとの会話に貼って影響度を判断してください。"
        ),
    }


def format_markdown(report: dict) -> str:
    title = f"{report['ticker']}（{report['name']}）" if report.get("name") else report["ticker"]
    price_tag = "（moomooリアルタイム）" if report.get("price_source") == "moomoo_realtime" else "（yfinance・遅延あり）"
    lines = [f"# {title} 総合見通しレポート", "", f"現在値: {report['price']} {price_tag}"]
    if report.get("sector"):
        lines.append(f"セクター: {report['sector']}")
    if report.get("return_20d") is not None:
        rs = report.get("relative_strength_20d")
        rs_text = f" (セクター比 {rs:+.2f}pt)" if rs is not None else ""
        lines.append(f"20営業日騰落率: {report['return_20d']:+.2f}%{rs_text}")
    if report.get("next_earnings_date"):
        lines.append(f"次回決算予定日: {report['next_earnings_date']}")
    lines.append("")

    lines.append("## テクニカル分析（個別銘柄）")
    for key, jp in _TERMS:
        t = report["technical"][key]
        lines.append(f"- {jp}: {t['label']} (score: {t['score']})")

    lines.append("")
    lines.append(f"## マクロ指数（{report['macro_index']['name']}）の同時テクニカル")
    for key, jp in _TERMS:
        t = report["macro_index"]["outlook"][key]
        lines.append(f"- {jp}: {t['label']} (score: {t['score']})")

    lines.append("")
    lines.append("## 総合見通し（個別70% + 指数30%）")
    for key, jp in _TERMS:
        c = report["combined_technical_macro"][key]
        lines.append(f"- {jp}: {c['label']} (score: {c['score']})")

    lines.append("")
    lines.append(f"## ファンダメンタルズ材料（{report['fundamentals_source']}、自動採点なし）")
    for item in report["fundamentals_raw"]:
        lines.append(f"- [{item.get('published_at', '')}] {item.get('title', '')}")

    lines.append("")
    lines.append(f"> {report['fundamentals_note']}")
    return "\n".join(lines)


def save_report(report: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_markdown(report), encoding="utf-8")
    return path
