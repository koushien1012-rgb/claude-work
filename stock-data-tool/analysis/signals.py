import numpy as np
import pandas as pd


def _score_rsi(value: float) -> float:
    if pd.isna(value):
        return 0.0
    if value >= 70:
        return -0.5
    if value <= 30:
        return 0.5
    return float(np.clip((value - 50) / 50 * 0.6, -1, 1))


def _score_stochastic(k: float, d: float) -> float:
    if pd.isna(k) or pd.isna(d):
        return 0.0
    if k > 80:
        return -0.5
    if k < 20:
        return 0.5
    return 0.3 if k > d else -0.3


def _score_macd_hist(hist_series: pd.Series, price: float) -> float:
    if len(hist_series) < 2 or price == 0:
        return 0.0
    latest, prev = hist_series.iloc[-1], hist_series.iloc[-2]
    if pd.isna(latest) or pd.isna(prev):
        return 0.0
    level = np.clip((latest / price * 100) * 10, -1, 1)
    momentum = 0.3 if latest > prev else -0.3
    return float(np.clip(level * 0.7 + momentum, -1, 1))


def _score_macd_trend(macd_val: float, signal_val: float, price: float) -> float:
    if pd.isna(macd_val) or pd.isna(signal_val) or price == 0:
        return 0.0
    diff_pct = (macd_val - signal_val) / price * 100
    return float(np.clip(diff_pct * 10, -1, 1))


def _score_ma_cross(short_ma: float, long_ma: float) -> float:
    if pd.isna(short_ma) or pd.isna(long_ma) or long_ma == 0:
        return 0.0
    diff_ratio = (short_ma - long_ma) / long_ma
    return float(np.clip(diff_ratio * 20, -1, 1))


def _score_price_vs_ma(price: float, ma: float) -> float:
    if pd.isna(ma) or ma == 0:
        return 0.0
    diff_ratio = (price - ma) / ma
    return float(np.clip(diff_ratio * 20, -1, 1))


def _score_bollinger(price: float, upper: float, mid: float, lower: float) -> float:
    if pd.isna(upper) or pd.isna(lower) or upper == lower:
        return 0.0
    half_width = (upper - lower) / 2
    return float(np.clip((price - mid) / half_width, -1, 1))


def _score_adx_trend(plus_di: float, minus_di: float, adx_val: float) -> float:
    if pd.isna(adx_val) or pd.isna(plus_di) or pd.isna(minus_di):
        return 0.0
    direction = 1 if plus_di > minus_di else -1
    strength = min(adx_val / 50, 1.0)
    return float(direction * strength)


def _score_volume_confirmation(close: pd.Series, obv: pd.Series, window: int = 10) -> float:
    if len(close) < window + 1 or len(obv) < window + 1:
        return 0.0
    price_chg = close.iloc[-1] - close.iloc[-window]
    obv_chg = obv.iloc[-1] - obv.iloc[-window]
    if pd.isna(price_chg) or pd.isna(obv_chg):
        return 0.0
    price_up = price_chg > 0
    obv_up = obv_chg > 0
    if price_up and obv_up:
        return 1.0
    if not price_up and not obv_up:
        return -1.0
    return -0.3 if price_up else 0.3


def _score_ichimoku(price: float, senkou_a: float, senkou_b: float) -> float:
    if pd.isna(senkou_a) or pd.isna(senkou_b):
        return 0.0
    cloud_top = max(senkou_a, senkou_b)
    cloud_bottom = min(senkou_a, senkou_b)
    if price > cloud_top:
        return 1.0
    if price < cloud_bottom:
        return -1.0
    return 0.0


def _label(score: float) -> str:
    if score >= 0.5:
        return "強気（上昇優勢）"
    if score >= 0.25:
        return "やや強気"
    if score > -0.25:
        return "中立"
    if score > -0.5:
        return "やや弱気"
    return "弱気（下落優勢）"


def label_for_score(score: float) -> str:
    return _label(score)


# 移動平均線ベースの指標を主、オシレーター系を副として重み付け
SHORT_TERM_WEIGHTS = {
    "price_vs_sma5": 2.0,
    "macd_momentum": 1.5,
    "rsi14": 1.0,
    "stochastic": 1.0,
    "bollinger_position": 1.0,
    "volume_confirmation": 1.0,
}
MID_TERM_WEIGHTS = {
    "sma25_vs_sma75": 2.0,
    "price_vs_sma25": 2.0,
    "macd_trend": 1.5,
    "adx_trend": 1.0,
    "volume_confirmation": 0.75,
}
LONG_TERM_WEIGHTS = {
    "sma75_vs_sma200": 2.0,
    "price_vs_sma200": 2.0,
    "ichimoku_cloud": 1.5,
    "adx_trend": 1.0,
}


def _summarize(scores: dict, weights: dict) -> dict:
    if not scores:
        return {"score": 0.0, "label": _label(0.0), "details": {}}
    total_weight = sum(weights[k] for k in scores)
    avg = sum(scores[k] * weights[k] for k in scores) / total_weight
    return {"score": round(avg, 3), "label": _label(avg), "details": {k: round(v, 3) for k, v in scores.items()}}


def outlook(indicators: dict, df: pd.DataFrame) -> dict:
    price = float(df["close"].iloc[-1])
    sma_row = indicators["sma"].iloc[-1]
    rsi_val = indicators["rsi14"].iloc[-1]
    stoch_row = indicators["stochastic"].iloc[-1]
    macd_df = indicators["macd"]
    macd_row = macd_df.iloc[-1]
    bb_row = indicators["bollinger"].iloc[-1]
    adx_row = indicators["adx"].iloc[-1]
    ichi_row = indicators["ichimoku"].iloc[-1]

    volume_short = _score_volume_confirmation(df["close"], indicators["obv"], window=10)
    volume_mid = _score_volume_confirmation(df["close"], indicators["obv"], window=25)

    short_scores = {
        "rsi14": _score_rsi(rsi_val),
        "stochastic": _score_stochastic(stoch_row["%K"], stoch_row["%D"]),
        "macd_momentum": _score_macd_hist(macd_df["hist"], price),
        "price_vs_sma5": _score_price_vs_ma(price, sma_row["sma5"]),
        "bollinger_position": _score_bollinger(price, bb_row["upper"], bb_row["mid"], bb_row["lower"]),
        "volume_confirmation": volume_short,
    }
    mid_scores = {
        "sma25_vs_sma75": _score_ma_cross(sma_row["sma25"], sma_row["sma75"]),
        "price_vs_sma25": _score_price_vs_ma(price, sma_row["sma25"]),
        "macd_trend": _score_macd_trend(macd_row["macd"], macd_row["signal"], price),
        "adx_trend": _score_adx_trend(adx_row["+DI"], adx_row["-DI"], adx_row["ADX"]),
        "volume_confirmation": volume_mid,
    }
    long_scores = {
        "sma75_vs_sma200": _score_ma_cross(sma_row["sma75"], sma_row["sma200"]),
        "price_vs_sma200": _score_price_vs_ma(price, sma_row["sma200"]),
        "ichimoku_cloud": _score_ichimoku(price, ichi_row["senkou_a"], ichi_row["senkou_b"]),
        "adx_trend": _score_adx_trend(adx_row["+DI"], adx_row["-DI"], adx_row["ADX"]),
    }

    return {
        "price": price,
        "short_term": _summarize(short_scores, SHORT_TERM_WEIGHTS),
        "mid_term": _summarize(mid_scores, MID_TERM_WEIGHTS),
        "long_term": _summarize(long_scores, LONG_TERM_WEIGHTS),
    }
