import json
import math
from datetime import date, datetime
from pathlib import Path

from analysis import generate_report

SECTOR_TICKERS: dict[str, dict[str, list[str]]] = {
    "宇宙": {
        "us": ["SPCX", "RKLB", "ASTS", "LUNR"],
        "jp": ["9348.T", "7013.T", "7011.T", "464A.T"],
    },
    "防衛": {
        "us": ["LMT", "RTX", "NOC", "GD"],
        "jp": ["7011.T", "7012.T", "7013.T", "5631.T"],
    },
    "船舶": {
        "us": ["ZIM", "FRO", "GOGL", "GNK"],
        "jp": ["9101.T", "9104.T", "9107.T", "7003.T"],
    },
    "メモリ半導体": {
        "us": ["MU", "WDC", "SNDK", "STX"],
        "jp": ["285A.T", "8035.T", "6857.T", "6146.T"],
    },
}

NAME_MAP: dict[str, str] = {
    "SPCX": "SpaceX", "RKLB": "Rocket Lab", "ASTS": "AST SpaceMobile", "LUNR": "Intuitive Machines",
    "LMT": "Lockheed Martin", "RTX": "RTX Corporation", "NOC": "Northrop Grumman", "GD": "General Dynamics",
    "ZIM": "Zim Integrated Shipping", "FRO": "Frontline", "GOGL": "Golden Ocean Group", "GNK": "Genco Shipping",
    "MU": "Micron Technology", "WDC": "Western Digital", "SNDK": "SanDisk", "STX": "Seagate Technology",
    "9348.T": "ispace", "7013.T": "IHI", "7011.T": "三菱重工業", "464A.T": "QPSホールディングス",
    "7012.T": "川崎重工業", "5631.T": "日本製鋼所",
    "9101.T": "日本郵船", "9104.T": "商船三井", "9107.T": "川崎汽船", "7003.T": "三井E&S",
    "285A.T": "キオクシアHD", "8035.T": "東京エレクトロン", "6857.T": "アドバンテスト", "6146.T": "ディスコ",
}


def dedupe_tickers(sector_tickers: dict) -> list[dict]:
    seen: set[str] = set()
    result = []
    for markets in sector_tickers.values():
        for market, tickers in markets.items():
            for ticker in tickers:
                if ticker in seen:
                    continue
                seen.add(ticker)
                result.append({"ticker": ticker, "market": market})
    return result


def _avg_score(technical: dict) -> float:
    scores = [technical["short_term"]["score"], technical["mid_term"]["score"], technical["long_term"]["score"]]
    return sum(scores) / len(scores)


def _build_entry(ticker: str, report: dict, score_change: float | None = None) -> dict:
    return {
        "ticker": ticker,
        "name": report.get("name") or "",
        "name_ja": None,
        "price": report["price"],
        "price_source": report.get("price_source", "yfinance"),
        "technical": report["technical"],
        "fundamentals_source": report.get("fundamentals_source"),
        "fundamentals_raw": report.get("fundamentals_raw") or [],
        "score_change": score_change,
    }


def build_sector_payload(sector_tickers: dict, reports_by_ticker: dict, score_changes: dict | None = None) -> list[dict]:
    score_changes = score_changes or {}
    payload = []
    for sector, markets in sector_tickers.items():
        section = {"name": sector}
        for market, tickers in markets.items():
            section[market] = [
                _build_entry(ticker, reports_by_ticker[ticker], score_changes.get(ticker))
                for ticker in tickers
                if ticker in reports_by_ticker
            ]
        payload.append(section)
    return payload


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def load_previous_snapshot(history_dir: Path, today: str) -> dict | None:
    if not history_dir.exists():
        return None
    candidates = sorted(p.stem for p in history_dir.glob("*.json") if p.stem < today)
    if not candidates:
        return None
    latest = candidates[-1]
    return json.loads((history_dir / f"{latest}.json").read_text(encoding="utf-8"))


def save_snapshot(history_dir: Path, today: str, snapshot: dict) -> None:
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / f"{today}.json").write_text(
        json.dumps(_sanitize(snapshot), ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )


def main():
    today = date.today().isoformat()
    history_dir = Path("output/sector_watchlist_history")
    previous = load_previous_snapshot(history_dir, today)

    tickers = dedupe_tickers(SECTOR_TICKERS)
    reports_by_ticker = {}
    snapshot = {}
    for item in tickers:
        ticker = item["ticker"]
        try:
            report = generate_report(ticker, name=NAME_MAP.get(ticker))
            reports_by_ticker[ticker] = report
            snapshot[ticker] = _avg_score(report["technical"])
        except Exception as exc:
            print(f"failed to build report for {ticker}: {exc}")

    if not reports_by_ticker:
        print(f"aborting: 0/{len(tickers)} tickers fetched successfully, leaving existing dashboard data untouched")
        raise SystemExit(1)

    save_snapshot(history_dir, today, snapshot)

    score_changes = {}
    if previous:
        for ticker, avg in snapshot.items():
            prev = previous.get(ticker)
            if prev is not None:
                score_changes[ticker] = round(avg - prev, 4)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fetched": len(reports_by_ticker),
        "expected": len(tickers),
        "sectors": build_sector_payload(SECTOR_TICKERS, reports_by_ticker, score_changes),
    }

    out_path = Path("dashboard/sector_watchlist_data.json")
    out_path.write_text(
        json.dumps(_sanitize(payload), ensure_ascii=False, indent=2, default=str, allow_nan=False),
        encoding="utf-8",
    )
    print(f"wrote {out_path} ({len(reports_by_ticker)}/{len(tickers)} tickers)")


if __name__ == "__main__":
    main()
