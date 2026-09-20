import requests
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0 (research script; stock-data-tool)"}


def get_rss_headlines(url: str, limit: int = 20) -> list[dict]:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "xml")
    items = []
    for it in soup.find_all("item")[:limit]:
        title = it.title.get_text(strip=True) if it.title else ""
        link = it.link.get_text(strip=True) if it.link else ""
        pub_date = it.pubDate.get_text(strip=True) if it.pubDate else ""
        desc_tag = it.find("description")
        summary = desc_tag.get_text(strip=True) if desc_tag else ""
        items.append({
            "title": title,
            "summary": summary,
            "link": link,
            "published_at": pub_date,
        })
    return items
