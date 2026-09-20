def get_us_realtime_snapshot(tickers: list[str], host: str = "127.0.0.1", port: int = 11111) -> dict:
    """Fetch real-time snapshots for US tickers via a locally running moomoo OpenD.

    Returns {ticker: {"price": float, "change_pct": float}} for tickers moomoo could
    price. Returns an empty dict (no error) if moomoo-api is not installed or OpenD
    is not reachable, so callers can silently fall back to another data source.
    """
    try:
        from moomoo import OpenQuoteContext, RET_OK
    except ImportError:
        return {}

    if not tickers:
        return {}

    code_map = {f"US.{t}": t for t in tickers}
    result = {}
    try:
        ctx = OpenQuoteContext(host=host, port=port)
    except Exception:
        return {}

    try:
        for i in range(0, len(tickers), 400):
            batch_codes = list(code_map.keys())[i:i + 400]
            ret, data = ctx.get_market_snapshot(batch_codes)
            if ret != RET_OK:
                continue
            for _, row in data.iterrows():
                ticker = code_map.get(row["code"])
                if not ticker:
                    continue
                last = row.get("last_price")
                prev_close = row.get("prev_close_price")
                if last is None or not prev_close:
                    continue
                change_pct = (last - prev_close) / prev_close * 100
                result[ticker] = {"price": float(last), "change_pct": round(float(change_pct), 2)}
    except Exception:
        return result
    finally:
        try:
            ctx.close()
        except Exception:
            pass
    return result
