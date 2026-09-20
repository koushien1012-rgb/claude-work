import pandas as pd


def compute_phase(df: pd.DataFrame, range_window: int = 20, lookback: int = 60) -> dict:
    """Wyckoff-style phase heuristic from range compression/expansion and volume."""
    if len(df) < lookback:
        return {"phase": "undefined", "since": None}

    recent = df.iloc[-lookback:]
    range_high = recent["high"].rolling(range_window).max()
    range_low = recent["low"].rolling(range_window).min()
    range_width = (range_high - range_low) / range_low

    prior_mean = range_width.iloc[:-range_window].mean()
    is_tight_range = bool(range_width.iloc[-1] < prior_mean * 0.7) if pd.notna(prior_mean) else False

    price = recent["close"].iloc[-1]
    range_mid = (range_high.iloc[-1] + range_low.iloc[-1]) / 2
    vol_avg_recent = recent["volume"].iloc[-range_window:].mean()
    vol_avg_prior = recent["volume"].iloc[:-range_window].mean() if len(recent) > range_window else vol_avg_recent
    volume_rising = vol_avg_recent > vol_avg_prior

    broke_up = price > range_high.iloc[-range_window]
    broke_down = price < range_low.iloc[-range_window]

    if broke_up and volume_rising:
        phase = "markup"
    elif broke_down and volume_rising:
        phase = "markdown"
    elif is_tight_range and price <= range_mid:
        phase = "accumulation"
    elif is_tight_range and price > range_mid:
        phase = "distribution"
    else:
        phase = "undefined"

    since = recent.index[-range_window]
    return {"phase": phase, "since": since}
