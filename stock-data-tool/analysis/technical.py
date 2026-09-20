import numpy as np
import pandas as pd

from . import candlestick, dow_theory, fibonacci, volume_profile, wyckoff


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    mid = sma(series, window)
    std = series.rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"upper": upper, "mid": mid, "lower": lower})


def stochastic(df: pd.DataFrame, k_window: int = 14, d_window: int = 3) -> pd.DataFrame:
    low_min = df["low"].rolling(k_window).min()
    high_max = df["high"].rolling(k_window).max()
    percent_k = 100 * (df["close"] - low_min) / (high_max - low_min)
    percent_d = percent_k.rolling(d_window).mean()
    return pd.DataFrame({"%K": percent_k, "%D": percent_d})


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    prev_close = df["close"].shift()
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff()).fillna(0)
    return (direction * df["volume"]).cumsum()


def adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    up_move = df["high"].diff()
    down_move = -df["low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr_atr = atr(df, window)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / window, min_periods=window, adjust=False).mean() / tr_atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / window, min_periods=window, adjust=False).mean() / tr_atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_line = dx.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    return pd.DataFrame({"+DI": plus_di, "-DI": minus_di, "ADX": adx_line})


def ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    tenkan = (df["high"].rolling(9).max() + df["low"].rolling(9).min()) / 2
    kijun = (df["high"].rolling(26).max() + df["low"].rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((df["high"].rolling(52).max() + df["low"].rolling(52).min()) / 2).shift(26)
    chikou = df["close"].shift(-26)
    return pd.DataFrame({
        "tenkan": tenkan,
        "kijun": kijun,
        "senkou_a": senkou_a,
        "senkou_b": senkou_b,
        "chikou": chikou,
    })


def _resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("W").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
    }).dropna()


def compute_indicators(df: pd.DataFrame) -> dict:
    close = df["close"]
    daily_swings = dow_theory.find_swings(df, window=5)
    weekly_df = _resample_weekly(df)
    if len(weekly_df) > 10:
        dow_weekly = dow_theory.analyze(weekly_df, window=3)
    else:
        dow_weekly = {"trend": "sideways", "last_swings": [], "confirmed_by_volume": False}

    return {
        "sma": pd.DataFrame({
            "sma5": sma(close, 5),
            "sma25": sma(close, 25),
            "sma75": sma(close, 75),
            "sma200": sma(close, 200),
        }),
        "ema": pd.DataFrame({
            "ema12": ema(close, 12),
            "ema26": ema(close, 26),
        }),
        "rsi14": rsi(close, 14),
        "macd": macd(close),
        "bollinger": bollinger_bands(close),
        "stochastic": stochastic(df),
        "atr14": atr(df),
        "obv": obv(df),
        "adx": adx(df),
        "ichimoku": ichimoku(df),
        "dow_daily": dow_theory.analyze(df, window=5),
        "dow_weekly": dow_weekly,
        "wyckoff": wyckoff.compute_phase(df),
        "candlestick": candlestick.detect_pattern(df),
        "fibonacci": fibonacci.evaluate(df, daily_swings),
        "volume_profile": volume_profile.compute_profile(df),
    }
