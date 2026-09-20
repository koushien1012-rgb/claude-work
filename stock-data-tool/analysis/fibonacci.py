import pandas as pd

_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


def compute_levels(swing_high: float, swing_low: float) -> dict[float, float]:
    diff = swing_high - swing_low
    return {level: round(swing_high - diff * level, 4) for level in _LEVELS}


def evaluate(df: pd.DataFrame, swings: list[dict]) -> dict:
    highs = [s for s in swings if s["type"] == "high"]
    lows = [s for s in swings if s["type"] == "low"]
    if not highs or not lows:
        return {"levels": {}, "price_zone": "unknown", "score": 0.0}

    last_high, last_low = highs[-1], lows[-1]
    swing_high = max(last_high["price"], last_low["price"])
    swing_low = min(last_high["price"], last_low["price"])
    levels = compute_levels(swing_high, swing_low)
    price = float(df["close"].iloc[-1])

    diff = swing_high - swing_low
    if diff == 0:
        return {"levels": levels, "price_zone": "unknown", "score": 0.0}

    position = (price - swing_low) / diff
    score = 1.0 - min(abs(position - 0.5) / 0.5, 1.0)
    closest_level = min(levels.items(), key=lambda kv: abs(kv[1] - price))
    return {"levels": levels, "price_zone": f"{closest_level[0]:.3f}", "score": round(score, 3)}
