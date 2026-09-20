import json
from pathlib import Path

from news import get_rss_headlines

_CONFIG_PATH = Path("watched_figures.json")

_RSS_SOURCES = {
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "MarketWatch市況": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
    "CNBC政治": "https://www.cnbc.com/id/10000113/device/rss/rss.html",
    "CNBC経済": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
}


def load_watched_figures() -> list[str]:
    if not _CONFIG_PATH.exists():
        return []
    data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    return data.get("figures", [])


def _extract_mentioned_tickers(text: str, name_map: dict, limit: int = 5) -> list[str]:
    text_lower = text.lower()
    hits = []
    for ticker, name in name_map.items():
        if not name or len(name) < 3:
            continue
        if name.lower() in text_lower:
            hits.append(ticker)
        if len(hits) >= limit:
            break
    return hits


def get_figure_mentions(names: list[str] | None = None, name_map: dict | None = None,
                         limit_per_source: int = 20) -> list[dict]:
    names = names if names is not None else load_watched_figures()
    if not names:
        return []
    name_map = name_map or {}
    lower_names = [n.lower() for n in names]

    matched = []
    for source_label, url in _RSS_SOURCES.items():
        try:
            items = get_rss_headlines(url, limit=limit_per_source)
        except Exception:
            continue
        for item in items:
            text = f"{item.get('title', '')} {item.get('summary', '')}"
            text_lower = text.lower()
            hit_names = [n for n, ln in zip(names, lower_names) if ln in text_lower]
            if not hit_names:
                continue
            matched.append({
                **item,
                "source": source_label,
                "matched_figures": hit_names,
                "related_tickers": _extract_mentioned_tickers(text, name_map),
            })
    return matched
