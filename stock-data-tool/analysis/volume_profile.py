import numpy as np
import pandas as pd


def compute_profile(df: pd.DataFrame, bins: int = 20, window: int = 120) -> dict:
    recent = df.iloc[-window:] if len(df) > window else df
    prices = recent["close"].to_numpy()
    volumes = recent["volume"].to_numpy()
    if len(prices) == 0:
        return {"poc": None, "value_area": (None, None), "price_vs_poc": 0.0}

    price_min, price_max = prices.min(), prices.max()
    if price_max == price_min:
        poc = float(price_min)
        return {"poc": poc, "value_area": (poc, poc), "price_vs_poc": 0.0}

    bin_edges = np.linspace(price_min, price_max, bins + 1)
    bin_volumes = np.zeros(bins)
    bin_indices = np.clip(np.digitize(prices, bin_edges) - 1, 0, bins - 1)
    for idx, vol in zip(bin_indices, volumes):
        bin_volumes[idx] += vol

    poc_bin = int(np.argmax(bin_volumes))
    poc = float((bin_edges[poc_bin] + bin_edges[poc_bin + 1]) / 2)

    total_volume = bin_volumes.sum()
    target = total_volume * 0.7
    order = np.argsort(bin_volumes)[::-1]
    covered = 0.0
    included_bins = []
    for idx in order:
        covered += bin_volumes[idx]
        included_bins.append(idx)
        if covered >= target:
            break
    value_area_low = float(bin_edges[min(included_bins)])
    value_area_high = float(bin_edges[max(included_bins) + 1])

    current_price = float(prices[-1])
    price_vs_poc = round((current_price - poc) / poc, 4) if poc else 0.0

    return {
        "poc": round(poc, 4),
        "value_area": (round(value_area_low, 4), round(value_area_high, 4)),
        "price_vs_poc": price_vs_poc,
    }
