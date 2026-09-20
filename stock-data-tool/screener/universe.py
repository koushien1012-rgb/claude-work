import io
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

_CACHE_DIR = Path(__file__).resolve().parent.parent / "output" / "cache"
_CACHE_TTL_SECONDS = 7 * 24 * 3600  # refresh weekly
_HEADERS = {"User-Agent": "Mozilla/5.0 (research script; stock-data-tool)"}

_GICS_SECTOR_JA = {
    "Information Technology": "情報技術",
    "Health Care": "ヘルスケア",
    "Financials": "金融",
    "Consumer Discretionary": "一般消費財",
    "Communication Services": "通信サービス",
    "Industrials": "資本財",
    "Consumer Staples": "生活必需品",
    "Energy": "エネルギー",
    "Utilities": "公益事業",
    "Real Estate": "不動産",
    "Materials": "素材",
}


def _read_cache(name: str) -> list | None:
    path = _CACHE_DIR / f"{name}.json"
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > _CACHE_TTL_SECONDS:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_cache(name: str, data: list) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (_CACHE_DIR / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def get_sp500_info(use_cache: bool = True) -> list[dict]:
    if use_cache:
        cached = _read_cache("sp500_info")
        if cached:
            return cached
    resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    df = pd.read_html(io.StringIO(resp.text))[0]
    records = [
        {
            "ticker": str(row["Symbol"]).replace(".", "-"),
            "name": str(row["Security"]),
            "sector": _GICS_SECTOR_JA.get(str(row["GICS Sector"]), str(row["GICS Sector"])),
        }
        for _, row in df.iterrows()
    ]
    _write_cache("sp500_info", records)
    return records


def get_sp500_tickers(use_cache: bool = True) -> list[str]:
    return [r["ticker"] for r in get_sp500_info(use_cache)]


def get_nikkei225_info(use_cache: bool = True) -> list[dict]:
    if use_cache:
        cached = _read_cache("nikkei225_info")
        if cached:
            return cached
    resp = requests.get("https://ja.wikipedia.org/wiki/日経平均株価", headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    records = []
    for table in soup.select("table.wikitable"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        if header_cells != ["証券コード", "銘柄", "備考"]:
            continue
        heading_tag = table.find_previous(["h2", "h3", "h4"])
        heading = heading_tag.get_text(strip=True) if heading_tag else ""
        sector = re.sub(r"（\d+銘柄）", "", heading).strip()
        for tr in rows[1:]:
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) < 2:
                continue
            code_match = re.search(r"(\d{4})", cells[0])
            if not code_match:
                continue
            records.append({"ticker": f"{code_match.group(1)}.T", "name": cells[1], "sector": sector})
    if not records:
        raise RuntimeError("Nikkei 225 constituent table not found on Wikipedia page.")
    _write_cache("nikkei225_info", records)
    return records


def get_nikkei225_tickers(use_cache: bool = True) -> list[str]:
    return [r["ticker"] for r in get_nikkei225_info(use_cache)]


def get_name_map(use_cache: bool = True) -> dict:
    records = get_sp500_info(use_cache) + get_nikkei225_info(use_cache)
    return {r["ticker"]: r["name"] for r in records}
