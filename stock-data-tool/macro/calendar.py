import io
import re
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0 (research script; stock-data-tool)"}
_FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
_BOJ_URL = "https://www.boj.or.jp/mopo/mpmsche_minu/index.htm"

_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


def get_fomc_dates(year: int) -> list[dict]:
    resp = requests.get(_FOMC_URL, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    text = soup.get_text("\n")
    start = text.find(f"{year} FOMC Meetings")
    if start == -1:
        return []
    next_section = re.search(r"\d{4} FOMC Meetings", text[start + 1:])
    end = start + 1 + next_section.start() if next_section else -1
    section = text[start:end] if end != -1 else text[start:start + 4000]
    lines = [ln.strip() for ln in section.split("\n") if ln.strip()]

    month_re = re.compile(r"^([A-Za-z]+)(?:/([A-Za-z]+))?$")
    day_re = re.compile(r"^(\d{1,2})-(\d{1,2})\*?$")

    results = []
    i = 0
    while i < len(lines) - 1:
        m = month_re.match(lines[i])
        if m and m.group(1) in _MONTHS:
            dm = day_re.match(lines[i + 1])
            if dm:
                month_num = _MONTHS[m.group(1)]
                start_day, end_day = int(dm.group(1)), int(dm.group(2))
                try:
                    start_date = date(year, month_num, start_day)
                    end_month = month_num if end_day >= start_day else (month_num % 12) + 1
                    end_date = date(year, end_month, end_day)
                    results.append({
                        "event": "FOMC会合",
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "source": _FOMC_URL,
                    })
                except ValueError:
                    pass
                i += 2
                continue
        i += 1
    return results


def get_boj_dates(year: int) -> list[dict]:
    resp = requests.get(_BOJ_URL, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    date_re = re.compile(r"(\d{1,2})月(\d{1,2})日(?:（.）)?(?:[・･](\d{1,2})日(?:（.）)?)?")

    for table in soup.find_all("table"):
        heading = table.find_previous(["h1", "h2", "h3", "h4"])
        heading_text = heading.get_text(strip=True) if heading else ""
        if f"{year}年" not in heading_text:
            continue
        df = pd.read_html(io.StringIO(str(table)))[0]
        results = []
        for cell in df.iloc[:, 0].astype(str):
            m = date_re.search(cell)
            if not m:
                continue
            month = int(m.group(1))
            start_day = int(m.group(2))
            end_day = int(m.group(3)) if m.group(3) else start_day
            try:
                start_date = date(year, month, start_day)
                end_date = date(year, month, end_day)
                results.append({
                    "event": "日銀金融政策決定会合",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "source": _BOJ_URL,
                })
            except ValueError:
                continue
        return results
    return []


def get_upcoming_events(today: date, years: tuple[int, ...] | None = None, within_days: int = 45,
                         recent_days: int = 3) -> list[dict]:
    years = years or (today.year, today.year + 1)
    events = []
    for year in years:
        try:
            events.extend(get_fomc_dates(year))
        except Exception:
            pass
        try:
            events.extend(get_boj_dates(year))
        except Exception:
            pass

    result = []
    for e in events:
        end = date.fromisoformat(e["end_date"])
        days_until = (end - today).days
        if -recent_days <= days_until <= within_days:
            status = "concluded" if days_until < 0 else "upcoming"
            result.append({**e, "days_until": days_until, "status": status})
    result.sort(key=lambda e: e["start_date"])
    return result
