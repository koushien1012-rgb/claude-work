import pandas as pd


def detect_pattern(df: pd.DataFrame) -> dict:
    """Detect a single dominant candlestick pattern on the latest bar(s)."""
    if len(df) < 2:
        return {"pattern": None, "direction": 0, "bar_index": None}
    prev, last = df.iloc[-2], df.iloc[-1]
    bar_index = len(df) - 1

    if (prev["close"] < prev["open"] and last["close"] > last["open"]
            and last["close"] >= prev["open"] and last["open"] <= prev["close"]):
        return {"pattern": "bullish_engulfing", "direction": 1, "bar_index": bar_index}

    if (prev["close"] > prev["open"] and last["close"] < last["open"]
            and last["open"] >= prev["close"] and last["close"] <= prev["open"]):
        return {"pattern": "bearish_engulfing", "direction": -1, "bar_index": bar_index}

    body = abs(last["close"] - last["open"])
    rng = last["high"] - last["low"]
    if rng > 0:
        lower_wick = min(last["open"], last["close"]) - last["low"]
        upper_wick = last["high"] - max(last["open"], last["close"])
        if body / rng < 0.35 and lower_wick / rng > 0.5 and upper_wick / rng < 0.15:
            direction = 1 if last["close"] >= last["open"] else -1
            return {"pattern": "hammer", "direction": direction, "bar_index": bar_index}
        if body / rng < 0.35 and upper_wick / rng > 0.5 and lower_wick / rng < 0.15:
            return {"pattern": "shooting_star", "direction": -1, "bar_index": bar_index}
        if body / rng < 0.1:
            return {"pattern": "doji", "direction": 0, "bar_index": bar_index}

    return {"pattern": None, "direction": 0, "bar_index": None}
