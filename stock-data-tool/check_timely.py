import json
from datetime import date
from pathlib import Path

from macro import get_figure_mentions, get_macro_news, get_upcoming_events
from screener import get_nikkei225_info, get_sp500_info

SEEN_PATH = Path("output/watchlist/timely_seen.json")
PENDING_PATH = Path("output/watchlist/timely_pending.json")


def _key(item: dict) -> str:
    return item.get("link") or ""


def _load_seen() -> set:
    if SEEN_PATH.exists():
        return set(json.loads(SEEN_PATH.read_text(encoding="utf-8")).get("seen", []))
    return set()


def _save_seen(seen: set) -> None:
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    trimmed = list(seen)[-2000:]
    SEEN_PATH.write_text(json.dumps({"seen": trimmed}, ensure_ascii=False), encoding="utf-8")


def main():
    name_map = {}
    try:
        info = get_nikkei225_info() + get_sp500_info()
        name_map = {r["ticker"]: r["name"] for r in info}
    except Exception:
        pass

    macro_news = get_macro_news()
    figure_mentions = get_figure_mentions(name_map=name_map)
    events = get_upcoming_events(date.today(), within_days=45, recent_days=1)
    concluded_events = [e for e in events if e["status"] == "concluded"]

    seen = _load_seen()
    pending = []

    for item in macro_news:
        key = _key(item)
        if key and key not in seen:
            pending.append({**item, "type": "macro_news"})

    for item in figure_mentions:
        key = _key(item)
        if key and key not in seen:
            pending.append({**item, "type": "figure_mention"})

    for e in concluded_events:
        key = f"event:{e['event']}:{e['end_date']}"
        if key not in seen:
            pending.append({**e, "type": "macro_event_result"})

    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_PATH.write_text(
        json.dumps(pending, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    for item in macro_news + figure_mentions:
        key = _key(item)
        if key:
            seen.add(key)
    for e in concluded_events:
        seen.add(f"event:{e['event']}:{e['end_date']}")
    _save_seen(seen)

    print(f"macro_news: {len(macro_news)}, figure_mentions: {len(figure_mentions)}, "
          f"concluded_events: {len(concluded_events)}")
    print(f"pending new items: {len(pending)}")


if __name__ == "__main__":
    main()
