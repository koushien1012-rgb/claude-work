import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0 (research script; stock-data-tool)"}
_BASE_URL = "https://fx.minkabu.jp/indicators"

_DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def parse_calendar_html(html: str) -> list[dict]:
    """Parse one week's page from fx.minkabu.jp/indicators into a flat list of indicator dicts."""
    soup = BeautifulSoup(html, "lxml")
    events = []

    for table in soup.select("table.tbl-border"):
        caption = table.find("caption")
        if not caption:
            continue
        m = _DATE_RE.search(caption.get_text())
        if not m:
            continue
        day = date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()

        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 8:
                continue
            time_text = cells[0].get_text(strip=True) or "未定"
            link = cells[2].find("a")
            indicator_name = link.get_text(strip=True) if link else cells[2].get_text(strip=True)
            indicator_url = f"https://fx.minkabu.jp{link['href']}" if link and link.get("href") else None
            country_name = indicator_name.split("・", 1)[0] if "・" in indicator_name else tr.get("data_country", "")

            importance_raw = tr.get("data_importance", "")
            try:
                importance = int(importance_raw)
            except ValueError:
                importance = 0

            events.append({
                "date": day,
                "time": time_text,
                "country": country_name,
                "country_code": tr.get("data_country", ""),
                "indicator_name": indicator_name,
                "indicator_url": indicator_url,
                "importance": importance,
                "prev_usdjpy_move": cells[4].get_text(strip=True) or None,
                "previous": cells[5].get_text(strip=True) or None,
                "forecast": cells[6].get_text(strip=True) or None,
                "result": cells[7].get_text(strip=True) or None,
            })
    return events


def get_calendar_week(anchor: date) -> list[dict]:
    resp = requests.get(_BASE_URL, params={"date": anchor.isoformat()}, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return parse_calendar_html(resp.text)


def get_calendar(today: date, within_days: int = 30) -> list[dict]:
    end_date = today + timedelta(days=within_days)
    seen = set()
    events = []

    cursor = today
    while cursor <= end_date:
        for e in get_calendar_week(cursor):
            key = (e["date"], e["time"], e["indicator_name"], e["indicator_url"])
            if key in seen:
                continue
            seen.add(key)
            events.append(e)
        cursor += timedelta(days=7)

    filtered = [e for e in events if today.isoformat() <= e["date"] <= end_date.isoformat()]
    filtered.sort(key=lambda e: (e["date"], e["time"] == "未定", e["time"]))
    return filtered
