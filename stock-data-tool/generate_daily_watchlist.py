import json
import math
import sys
import time
from datetime import date, datetime
from pathlib import Path

from analysis import generate_report, save_report
from macro import get_figure_mentions, get_macro_news, get_macro_snapshot, get_upcoming_events
from screener import check_watchlist_alerts, get_nikkei225_info, get_sp500_info, scan_universe, top_signals
from stock_data import get_us_realtime_snapshot

TOP_N = 10
WATCHLIST_PATH = Path("watchlist.json")


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _ticker_entry(ticker: str, report: dict) -> dict:
    return {
        "ticker": ticker,
        "name": report.get("name") or "",
        "name_ja": None,
        "sector": report.get("sector"),
        "return_20d": report.get("return_20d"),
        "relative_strength_20d": report.get("relative_strength_20d"),
        "next_earnings_date": report.get("next_earnings_date"),
        "price": report["price"],
        "price_source": report.get("price_source", "yfinance"),
        "intraday_change_pct": report.get("intraday_change_pct"),
        "technical": report["technical"],
        "macro_index": report["macro_index"],
        "combined": report["combined_technical_macro"],
        "fundamentals_source": report["fundamentals_source"],
        "fundamentals_raw": report["fundamentals_raw"],
        "claude_judgment": None,
    }


def _build_market_block(scan_df, bullish, bearish, name_map, reports_out, realtime_map=None):
    scan_lookup = scan_df.set_index("ticker")
    entries = {"bullish": [], "bearish": []}
    for key, df in (("bullish", bullish), ("bearish", bearish)):
        for ticker in df["ticker"]:
            try:
                row = scan_lookup.loc[ticker]
                report = generate_report(
                    ticker,
                    name=name_map.get(ticker),
                    sector=row.get("sector"),
                    return_20d=row.get("return_20d"),
                    relative_strength_20d=row.get("relative_strength_20d"),
                    realtime=(realtime_map or {}).get(ticker),
                )
                save_report(report, f"output/reports/{ticker.replace('.', '_')}.md")
                reports_out[ticker] = report
                entries[key].append(_ticker_entry(ticker, report))
            except Exception as exc:
                print(f"failed to build report for {ticker}: {exc}")
    return entries


def _load_watchlist() -> list[str]:
    if not WATCHLIST_PATH.exists():
        return []
    data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
    return data.get("tickers", [])


def main():
    run_type = sys.argv[1] if len(sys.argv) > 1 else "morning"
    start = time.time()
    nikkei_info = get_nikkei225_info()
    sp500_info = get_sp500_info()
    universe_info = nikkei_info + sp500_info
    universe = [r["ticker"] for r in universe_info]
    name_map = {r["ticker"]: r["name"] for r in universe_info}
    sector_map = {r["ticker"]: r["sector"] for r in universe_info}
    print(f"universe size: {len(universe)}")

    scan_df = scan_universe(universe, name_map=name_map, sector_map=sector_map, period="1y")
    print(f"scanned: {len(scan_df)} tickers in {time.time() - start:.1f}s")

    jp_tickers = {r["ticker"] for r in nikkei_info}
    is_jp = scan_df["ticker"].isin(jp_tickers)
    jp_scan_df = scan_df[is_jp]
    us_scan_df = scan_df[~is_jp]

    out_dir = Path("output/watchlist")
    out_dir.mkdir(parents=True, exist_ok=True)
    scan_df.to_csv(out_dir / "full_scan.csv", index=False)

    jp_bull, jp_bear = top_signals(jp_scan_df, n=TOP_N)
    us_bull, us_bear = top_signals(us_scan_df, n=TOP_N)

    us_picked_tickers = list(us_bull["ticker"]) + list(us_bear["ticker"])
    realtime_map = get_us_realtime_snapshot(us_picked_tickers)
    print(f"moomoo realtime prices: {len(realtime_map)}/{len(us_picked_tickers)} tickers "
          f"({'OpenD reachable' if realtime_map else 'unavailable, falling back to yfinance'})")

    reports = {}
    jp_entries = _build_market_block(jp_scan_df, jp_bull, jp_bear, name_map, reports)
    us_entries = _build_market_block(us_scan_df, us_bull, us_bear, name_map, reports, realtime_map=realtime_map)

    jp_bull.to_csv(out_dir / "top_bullish_jp.csv", index=False)
    jp_bear.to_csv(out_dir / "top_bearish_jp.csv", index=False)
    us_bull.to_csv(out_dir / "top_bullish_us.csv", index=False)
    us_bear.to_csv(out_dir / "top_bearish_us.csv", index=False)

    (out_dir / "picked_reports_raw.json").write_text(
        json.dumps(_sanitize(reports), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    watchlist_tickers = _load_watchlist()
    watchlist_alerts = check_watchlist_alerts(watchlist_tickers, name_map)

    macro_events = get_upcoming_events(date.today(), within_days=45)
    macro_news = get_macro_news()
    figure_mentions = get_figure_mentions(name_map=name_map)

    dashboard_data = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_type": run_type,
        "universe_size": len(universe),
        "macro_snapshot": get_macro_snapshot().to_dict(orient="records"),
        "macro_events": macro_events,
        "macro_news": macro_news,
        "figure_mentions": figure_mentions,
        "watchlist_alerts": watchlist_alerts,
        "markets": {
            "jp": jp_entries,
            "us": us_entries,
        },
    }
    (out_dir / "dashboard_data.json").write_text(
        json.dumps(_sanitize(dashboard_data), ensure_ascii=False, indent=2, default=str, allow_nan=False),
        encoding="utf-8",
    )

    history_dir = out_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "date": date.today().isoformat(),
        "run_type": run_type,
        "rows": scan_df[["ticker", "sector", "price", "short_score", "mid_score", "long_score", "avg_score"]]
        .to_dict(orient="records"),
    }
    (history_dir / f"{date.today().isoformat()}_{run_type}.json").write_text(
        json.dumps(_sanitize(snapshot), ensure_ascii=False, default=str, allow_nan=False), encoding="utf-8"
    )

    print(f"done in {time.time() - start:.1f}s")
    print(f"jp bullish: {list(jp_bull['ticker'])}")
    print(f"jp bearish: {list(jp_bear['ticker'])}")
    print(f"us bullish: {list(us_bull['ticker'])}")
    print(f"us bearish: {list(us_bear['ticker'])}")
    print(f"watchlist alerts: {len(watchlist_alerts)}")
    print(f"figure mentions: {len(figure_mentions)}")


if __name__ == "__main__":
    main()
