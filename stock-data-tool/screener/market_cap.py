import json
import time
from pathlib import Path

import yfinance as yf

from stock_data.moomoo_source import get_us_realtime_snapshot  # noqa: F401 (kept for symmetry/reference)

_CACHE_DIR = Path("output/cache")
_CACHE_TTL_SECONDS = 7 * 24 * 3600


def _read_cache(name: str) -> dict | None:
    path = _CACHE_DIR / f"{name}.json"
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > _CACHE_TTL_SECONDS:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_cache(name: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (_CACHE_DIR / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _get_us_market_caps_via_moomoo(tickers: list[str]) -> dict:
    try:
        from moomoo import OpenQuoteContext, RET_OK
    except ImportError:
        return {}
    code_map = {f"US.{t}": t for t in tickers}
    result = {}
    try:
        ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
    except Exception:
        return {}
    try:
        codes = list(code_map.keys())
        for i in range(0, len(codes), 400):
            batch = codes[i:i + 400]
            ret, data = ctx.get_market_snapshot(batch)
            if ret != RET_OK:
                continue
            for _, row in data.iterrows():
                ticker = code_map.get(row["code"])
                cap = row.get("total_market_val")
                if ticker and cap:
                    result[ticker] = float(cap)
    except Exception:
        pass
    finally:
        try:
            ctx.close()
        except Exception:
            pass
    return result


def _get_market_caps_via_yfinance(tickers: list[str]) -> dict:
    result = {}
    for ticker in tickers:
        try:
            cap = yf.Ticker(ticker).fast_info.get("marketCap")
            if cap:
                result[ticker] = float(cap)
        except Exception:
            continue
    return result


def get_market_caps(us_tickers: list[str], jp_tickers: list[str], use_cache: bool = True) -> dict:
    """Returns {ticker: market_cap_in_native_currency} for the given US and JP tickers.

    US caps come from moomoo (fast, batched, USD) when OpenD is reachable, otherwise
    fall back to yfinance. JP caps always come from yfinance (JPY) since moomoo does
    not yet cover the Japan market. Results are cached for a week.
    """
    cached = _read_cache("market_caps") if use_cache else None
    if cached:
        return cached

    us_caps = _get_us_market_caps_via_moomoo(us_tickers)
    missing_us = [t for t in us_tickers if t not in us_caps]
    if missing_us:
        us_caps.update(_get_market_caps_via_yfinance(missing_us))

    jp_caps = _get_market_caps_via_yfinance(jp_tickers)

    all_caps = {**us_caps, **jp_caps}
    _write_cache("market_caps", all_caps)
    return all_caps
