import pandas as pd


def _ohlcv_records(df: pd.DataFrame, window: int) -> list[dict]:
    recent = df.iloc[-window:] if len(df) > window else df
    return [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "open": round(float(row["open"]), 4),
            "high": round(float(row["high"]), 4),
            "low": round(float(row["low"]), 4),
            "close": round(float(row["close"]), 4),
            "volume": float(row["volume"]),
        }
        for idx, row in recent.iterrows()
    ]


def _swing_annotations(swings: list[dict], window_start) -> list[dict]:
    return [
        {"date": s["date"].strftime("%Y-%m-%d"), "price": s["price"], "type": s["type"]}
        for s in swings if s["date"] >= window_start
    ]


def build_chart_data(df: pd.DataFrame, swings: list[dict], fibonacci_levels: dict,
                      candlestick: dict, wyckoff_result: dict | None = None,
                      window: int = 180) -> dict:
    recent = df.iloc[-window:] if len(df) > window else df
    window_start = recent.index[0]

    fib_annotations = [{"level": level, "price": price} for level, price in fibonacci_levels.items()]

    candlestick_markers = []
    if candlestick.get("pattern"):
        last_date = df.index[-1]
        candlestick_markers.append({
            "date": last_date.strftime("%Y-%m-%d"),
            "pattern": candlestick["pattern"],
            "direction": candlestick["direction"],
        })

    wyckoff_zones = []
    if wyckoff_result and wyckoff_result.get("phase") not in (None, "undefined") and wyckoff_result.get("since") is not None:
        since = wyckoff_result["since"]
        wyckoff_zones.append({
            "start": max(since, window_start).strftime("%Y-%m-%d"),
            "end": df.index[-1].strftime("%Y-%m-%d"),
            "phase": wyckoff_result["phase"],
        })

    return {
        "ohlcv": _ohlcv_records(df, window),
        "annotations": {
            "swings": _swing_annotations(swings, window_start),
            "fibonacci_levels": fib_annotations,
            "wyckoff_zones": wyckoff_zones,
            "candlestick_markers": candlestick_markers,
        },
    }
