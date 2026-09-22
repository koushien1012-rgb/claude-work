import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd

from analysis.signals import label_for_score
from screener import CATEGORY_LABELS, CATEGORY_ORDER, categories_for_sector, get_market_caps
from stock_data import get_business_summary_en, get_next_earnings_date
from translate import business_summary_ja

SCAN_PATH = Path("output/watchlist/full_scan.csv")
OUT_PATH = Path("output/watchlist/sector_board.json")
TOP_N = 2


def _is_jp(ticker: str) -> bool:
    return str(ticker).endswith(".T")


def _score_block(row: pd.Series, prefix: str) -> dict:
    score = row.get(f"{prefix}_score")
    if pd.isna(score):
        return {"score": None, "label": None}
    return {"score": round(float(score), 3), "label": label_for_score(float(score))}


@lru_cache(maxsize=None)
def _business_summary_ja_cached(ticker: str) -> str | None:
    # a ticker can appear as a top-N pick in more than one category/sector within a single
    # run; memoize so it's only fetched/translated once per run (the on-disk cache in
    # translate.py already avoids re-translating across runs, but not within one run).
    return business_summary_ja(ticker, get_business_summary_en(ticker))


@lru_cache(maxsize=None)
def _next_earnings_date_cached(ticker: str) -> str | None:
    return get_next_earnings_date(ticker)


def _pick_to_dict(row: pd.Series) -> dict:
    ticker = row["ticker"]
    return {
        "ticker": ticker,
        "name": row.get("name") or "",
        "name_ja": None,
        "sector": row.get("sector"),
        "price": None if pd.isna(row.get("price")) else round(float(row["price"]), 2),
        "market_cap": None if pd.isna(row.get("market_cap")) else float(row["market_cap"]),
        "short_term": _score_block(row, "short"),
        "mid_term": _score_block(row, "mid"),
        "long_term": _score_block(row, "long"),
        "next_earnings_date": _next_earnings_date_cached(ticker),
        "business_summary_ja": _business_summary_ja_cached(ticker),
    }


def _top_n_by_cap(df: pd.DataFrame, n: int = TOP_N) -> list[dict]:
    ranked = df.dropna(subset=["market_cap"]).sort_values("market_cap", ascending=False).head(n)
    return [_pick_to_dict(row) for _, row in ranked.iterrows()]


def main():
    if not SCAN_PATH.exists():
        raise SystemExit(f"{SCAN_PATH} not found. Run generate_daily_watchlist.py first.")

    scan_df = pd.read_csv(SCAN_PATH)
    scan_df["is_jp"] = scan_df["ticker"].apply(_is_jp)

    jp_tickers = scan_df.loc[scan_df["is_jp"], "ticker"].tolist()
    us_tickers = scan_df.loc[~scan_df["is_jp"], "ticker"].tolist()
    print(f"jp tickers: {len(jp_tickers)}, us tickers: {len(us_tickers)}")

    market_caps = get_market_caps(us_tickers, jp_tickers)
    print(f"market caps resolved: {len(market_caps)}/{len(jp_tickers) + len(us_tickers)}")
    scan_df["market_cap"] = scan_df["ticker"].map(market_caps)

    scan_df["category_ids"] = scan_df["sector"].apply(categories_for_sector)

    jp_df = scan_df[scan_df["is_jp"]]
    us_df = scan_df[~scan_df["is_jp"]]

    categories = []
    for cat_id in CATEGORY_ORDER:
        jp_match = jp_df[jp_df["category_ids"].apply(lambda ids, c=cat_id: c in ids)]
        us_match = us_df[us_df["category_ids"].apply(lambda ids, c=cat_id: c in ids)]
        categories.append({
            "id": cat_id,
            "label": CATEGORY_LABELS[cat_id],
            "jp": _top_n_by_cap(jp_match),
            "us": _top_n_by_cap(us_match),
        })

    def _sector_groups(df: pd.DataFrame) -> list[dict]:
        groups = []
        for sector, group in df.groupby("sector"):
            if not sector or pd.isna(sector):
                continue
            picks = _top_n_by_cap(group)
            if picks:
                groups.append({"sector": sector, "picks": picks})
        groups.sort(key=lambda g: g["sector"])
        return groups

    sectors = {
        "jp": _sector_groups(jp_df),
        "us": _sector_groups(us_df),
    }

    output = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "categories": categories,
        "sectors": sectors,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
