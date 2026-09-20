import yfinance as yf


def get_news(ticker: str, limit: int = 10) -> list[dict]:
    raw = yf.Ticker(ticker).news or []
    items = []
    for entry in raw[:limit]:
        content = entry.get("content") if isinstance(entry.get("content"), dict) else entry
        provider = content.get("provider")
        canonical = content.get("canonicalUrl")
        items.append({
            "title": content.get("title"),
            "summary": content.get("summary") or content.get("description") or "",
            "publisher": provider.get("displayName") if isinstance(provider, dict) else entry.get("publisher"),
            "link": canonical.get("url") if isinstance(canonical, dict) else entry.get("link"),
            "published_at": content.get("pubDate") or entry.get("providerPublishTime"),
        })
    return items
