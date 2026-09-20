import pandas as pd


def find_swings(df: pd.DataFrame, window: int = 5) -> list[dict]:
    """Fractal-based swing high/low detection using a centered window."""
    swings = []
    highs, lows = df["high"], df["low"]
    n = len(df)
    for i in range(window, n - window):
        local_highs = highs.iloc[i - window:i + window + 1]
        local_lows = lows.iloc[i - window:i + window + 1]
        if highs.iloc[i] == local_highs.max():
            swings.append({"index": i, "date": df.index[i], "price": float(highs.iloc[i]), "type": "high"})
        elif lows.iloc[i] == local_lows.min():
            swings.append({"index": i, "date": df.index[i], "price": float(lows.iloc[i]), "type": "low"})
    return swings


def classify_trend(swings: list[dict]) -> str:
    """HH+HL -> up, LH+LL -> down, otherwise sideways."""
    highs = [s for s in swings if s["type"] == "high"][-2:]
    lows = [s for s in swings if s["type"] == "low"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "sideways"
    higher_high = highs[-1]["price"] > highs[-2]["price"]
    higher_low = lows[-1]["price"] > lows[-2]["price"]
    lower_high = highs[-1]["price"] < highs[-2]["price"]
    lower_low = lows[-1]["price"] < lows[-2]["price"]
    if higher_high and higher_low:
        return "up"
    if lower_high and lower_low:
        return "down"
    return "sideways"


def volume_confirms_trend(df: pd.DataFrame, trend: str, window: int = 10) -> bool:
    if trend == "sideways" or len(df) < window + 1:
        return False
    vol_chg = df["volume"].iloc[-1] - df["volume"].iloc[-window]
    return bool(vol_chg > 0)


def analyze(df: pd.DataFrame, window: int = 5) -> dict:
    swings = find_swings(df, window=window)
    trend = classify_trend(swings)
    confirmed = volume_confirms_trend(df, trend)
    return {"trend": trend, "last_swings": swings[-6:], "confirmed_by_volume": confirmed}
