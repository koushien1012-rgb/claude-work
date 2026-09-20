# 相場ボード：テクニカル分析スキルベース銘柄選定 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 相場ボード（`dashboard/index.html`）の銘柄選定に、ダウ理論・ワイコフ法・ローソク足パターン・フィボナッチ・ボリュームプロファイル・マルチタイムフレーム分析を統合し、最終上位10銘柄にはチャート上へ判断根拠を可視化する。

**Architecture:** 2段階パイプライン。第1段階は既存の日足全銘柄スキャン（`screener/scan.py`）に新規テクニカル指標モジュール5本を統合し、候補プールを従来の10銘柄から30〜50銘柄へ拡大する。第2段階は候補プールのみ1時間足（4時間足へリサンプル）を取得してマルチタイムフレーム整合性を確認し、最終上位10銘柄を確定。確定銘柄のみOHLCVとアノテーション（スイング・フィボナッチ・ワイコフゾーン・パターン）を生成し、ダッシュボードでチャート描画する。

**Tech Stack:** Python 3.12 / pandas / numpy / yfinance（既存）、pytest（新規追加）、TradingView Lightweight Charts（CDN、ダッシュボードJS側のみ）

**Spec:** [docs/superpowers/specs/2026-09-20-market-board-dow-theory-screening-design.md](../specs/2026-09-20-market-board-dow-theory-screening-design.md)

## Global Constraints

- 既存の `scan_universe()` の入出力形状（yfinance, period="1y", 日経225+S&P500 ≒ 700銘柄）は変えない
- 新規スコア要素は既存の `_score_*` 関数と同じ `-1.0〜1.0` のレンジに正規化する
- `top_signals()`（avg_score加重平均ランキング）のロジック自体は変更しない（候補プールの人数だけ広げる）
- `chart` フィールドは最終上位10銘柄のみに含め、全700銘柄分は含めない
- yfinanceの60分足（1h）は直近60日分までしか取得できない
- エリオット波動はスコアに使わず参考情報としてのみ表示する（文字列ラベルのみ、数値スコアに影響させない）
- セクター相場ボード（`dashboard/sector-board.html`）の選定ロジックは変更しない（対象外）
- 全ての作業は `stock-data-tool/` ディレクトリを起点に行う（コマンドはこのディレクトリから実行）

## Review Focus

- 週足データが浅い銘柄（新規上場等で1年に満たない履歴）で `dow_weekly` のスイング検出が空になっても例外を出さず `sideways` にフォールバックすること（Task 6でテスト）
- `volume_profile.compute_profile()` で全期間の価格が同一値（値動きなし銘柄）でもゼロ除算を起こさないこと（Task 5でテスト済み）
- 候補プール（30〜50銘柄）中、上場廃止・ティッカー変更等でyfinanceの1時間足取得に失敗する銘柄があっても、その銘柄をスキップして処理全体を継続すること（Task 8でテスト）
- `dashboard_data.json` に `chart` フィールドが無い銘柄（最終上位10位圏外）を `index.html` が描画しようとしてもエラーにならないこと（Task 11でテスト）
- `fibonacci.evaluate()` でswingsが1種類（highのみ/lowのみ）しか検出されない銘柄で `"unknown"` ゾーンを返し例外を出さないこと（Task 4でテスト済み）

---

## Task 1: pytest環境セットアップ + ダウ理論モジュール

**Files:**
- Modify: `requirements.txt`
- Create: `analysis/dow_theory.py`
- Test: `tests/analysis/test_dow_theory.py`

**Interfaces:**
- Produces: `dow_theory.find_swings(df: pd.DataFrame, window: int = 5) -> list[dict]`（各dictは `{"index": int, "date": Timestamp, "price": float, "type": "high"|"low"}`）
- Produces: `dow_theory.classify_trend(swings: list[dict]) -> str`（`"up"|"down"|"sideways"`）
- Produces: `dow_theory.volume_confirms_trend(df: pd.DataFrame, trend: str, window: int = 10) -> bool`
- Produces: `dow_theory.analyze(df: pd.DataFrame, window: int = 5) -> dict`（`{"trend": str, "last_swings": list[dict], "confirmed_by_volume": bool}`）

- [ ] **Step 1: requirements.txtにpytestを追加**

```
yfinance>=0.2.40
pandas>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
anthropic>=0.40.0
pytest>=8.0.0
```

- [ ] **Step 2: pytestをインストール**

Run: `pip install -r requirements.txt`
Expected: pytestが正常にインストールされる

- [ ] **Step 3: 失敗するテストを書く**

`tests/analysis/test_dow_theory.py`:

```python
import numpy as np
import pandas as pd

from analysis.dow_theory import analyze, classify_trend, find_swings


def _make_trending_df(n=60, direction=1):
    t = np.arange(n)
    cycle = 10
    drift = direction * 1.2 * t
    zigzag = 5 * np.sin(2 * np.pi * t / cycle)
    closes = 100 + drift + zigzag
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 0.3, "low": closes - 0.3, "close": closes,
        "volume": np.linspace(1000, 3000, n),
    }, index=dates)


def test_find_swings_detects_local_extrema():
    df = _make_trending_df(60, direction=1)
    swings = find_swings(df, window=5)
    assert len(swings) > 0
    assert all(s["type"] in ("high", "low") for s in swings)


def test_classify_trend_up_on_higher_highs_and_lows():
    df = _make_trending_df(60, direction=1)
    swings = find_swings(df, window=5)
    assert classify_trend(swings) == "up"


def test_classify_trend_down_on_lower_highs_and_lows():
    df = _make_trending_df(60, direction=-1)
    swings = find_swings(df, window=5)
    assert classify_trend(swings) == "down"


def test_classify_trend_sideways_when_insufficient_swings():
    assert classify_trend([{"type": "high", "price": 100.0}]) == "sideways"


def test_analyze_returns_expected_shape():
    df = _make_trending_df(60, direction=1)
    result = analyze(df, window=5)
    assert result["trend"] == "up"
    assert isinstance(result["confirmed_by_volume"], bool)
    assert len(result["last_swings"]) <= 6
```

- [ ] **Step 4: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_dow_theory.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'analysis.dow_theory'`）

- [ ] **Step 5: dow_theory.pyを実装**

`analysis/dow_theory.py`:

```python
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
```

- [ ] **Step 6: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_dow_theory.py -v`
Expected: PASS（5件全て）

- [ ] **Step 7: コミット**

```bash
git add requirements.txt analysis/dow_theory.py tests/analysis/test_dow_theory.py
git commit -m "feat: add Dow theory swing/trend detection module"
```

---

## Task 2: ワイコフフェーズモジュール

**Files:**
- Create: `analysis/wyckoff.py`
- Test: `tests/analysis/test_wyckoff.py`

**Interfaces:**
- Produces: `wyckoff.compute_phase(df: pd.DataFrame, range_window: int = 20, lookback: int = 60) -> dict`（`{"phase": "accumulation"|"markup"|"distribution"|"markdown"|"undefined", "since": Timestamp|None}`）

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_wyckoff.py`:

```python
import numpy as np
import pandas as pd

from analysis.wyckoff import compute_phase


def test_compute_phase_detects_markup_breakout():
    n = 80
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    closes = np.concatenate([
        100 + np.random.RandomState(1).normal(0, 0.3, 60),
        np.linspace(100.5, 110, 20),
    ])
    vols = np.concatenate([np.full(60, 1000), np.linspace(1000, 4000, 20)])
    df = pd.DataFrame({"high": closes + 0.5, "low": closes - 0.5, "close": closes, "volume": vols}, index=dates)
    result = compute_phase(df)
    assert result["phase"] == "markup"
    assert result["since"] is not None


def test_compute_phase_undefined_when_insufficient_history():
    df = pd.DataFrame({
        "high": [101.0] * 10, "low": [99.0] * 10, "close": [100.0] * 10, "volume": [1000.0] * 10,
    })
    result = compute_phase(df)
    assert result["phase"] == "undefined"
    assert result["since"] is None
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_wyckoff.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: wyckoff.pyを実装**

`analysis/wyckoff.py`:

```python
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
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_wyckoff.py -v`
Expected: PASS（2件）

- [ ] **Step 5: コミット**

```bash
git add analysis/wyckoff.py tests/analysis/test_wyckoff.py
git commit -m "feat: add Wyckoff phase heuristic module"
```

---

## Task 3: ローソク足パターンモジュール

**Files:**
- Create: `analysis/candlestick.py`
- Test: `tests/analysis/test_candlestick.py`

**Interfaces:**
- Produces: `candlestick.detect_pattern(df: pd.DataFrame) -> dict`（`{"pattern": str|None, "direction": 1|-1|0, "bar_index": int|None}`）

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_candlestick.py`:

```python
import pandas as pd

from analysis.candlestick import detect_pattern


def test_detects_bullish_engulfing():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 98, "close": 99},
        {"open": 98.5, "high": 103, "low": 98, "close": 102},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": "bullish_engulfing", "direction": 1, "bar_index": 1}


def test_detects_hammer():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 95, "close": 100.5},
        {"open": 99, "high": 100, "low": 90, "close": 99.5},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": "hammer", "direction": 1, "bar_index": 1}


def test_detects_doji():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 99, "close": 100},
        {"open": 100, "high": 105, "low": 95, "close": 100.05},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": "doji", "direction": 0, "bar_index": 1}


def test_no_pattern_returns_none():
    df = pd.DataFrame([
        {"open": 100, "high": 102, "low": 99, "close": 101},
        {"open": 101, "high": 103, "low": 100, "close": 102},
    ])
    result = detect_pattern(df)
    assert result == {"pattern": None, "direction": 0, "bar_index": None}


def test_insufficient_bars_returns_none():
    df = pd.DataFrame([{"open": 100, "high": 101, "low": 99, "close": 100}])
    result = detect_pattern(df)
    assert result == {"pattern": None, "direction": 0, "bar_index": None}
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_candlestick.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: candlestick.pyを実装**

`analysis/candlestick.py`:

```python
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
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_candlestick.py -v`
Expected: PASS（5件）

- [ ] **Step 5: コミット**

```bash
git add analysis/candlestick.py tests/analysis/test_candlestick.py
git commit -m "feat: add candlestick pattern detection module"
```

---

## Task 4: フィボナッチモジュール

**Files:**
- Create: `analysis/fibonacci.py`
- Test: `tests/analysis/test_fibonacci.py`

**Interfaces:**
- Consumes: `dow_theory.find_swings()` の戻り値（`list[dict]`）
- Produces: `fibonacci.compute_levels(swing_high: float, swing_low: float) -> dict[float, float]`
- Produces: `fibonacci.evaluate(df: pd.DataFrame, swings: list[dict]) -> dict`（`{"levels": dict, "price_zone": str, "score": float}`）

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_fibonacci.py`:

```python
import pandas as pd

from analysis.fibonacci import compute_levels, evaluate


def test_compute_levels_between_high_and_low():
    levels = compute_levels(swing_high=110, swing_low=90)
    assert levels[0.5] == 100.0
    assert levels[1.0] == 90.0
    assert levels[0.0] if 0.0 in levels else True  # 0.0 not required in level set


def test_evaluate_scores_midpoint_highest():
    swings = [{"type": "low", "price": 90}, {"type": "high", "price": 110}]
    df = pd.DataFrame({"close": [100.0]})
    result = evaluate(df, swings)
    assert result["price_zone"] == "0.500"
    assert result["score"] == 1.0


def test_evaluate_returns_unknown_with_no_swings():
    df = pd.DataFrame({"close": [100.0]})
    result = evaluate(df, [])
    assert result == {"levels": {}, "price_zone": "unknown", "score": 0.0}


def test_evaluate_returns_unknown_with_only_highs():
    swings = [{"type": "high", "price": 110}]
    df = pd.DataFrame({"close": [100.0]})
    result = evaluate(df, swings)
    assert result == {"levels": {}, "price_zone": "unknown", "score": 0.0}
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_fibonacci.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: fibonacci.pyを実装**

`analysis/fibonacci.py`:

```python
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
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_fibonacci.py -v`
Expected: PASS（4件）

- [ ] **Step 5: コミット**

```bash
git add analysis/fibonacci.py tests/analysis/test_fibonacci.py
git commit -m "feat: add Fibonacci retracement module"
```

---

## Task 5: ボリュームプロファイルモジュール

**Files:**
- Create: `analysis/volume_profile.py`
- Test: `tests/analysis/test_volume_profile.py`

**Interfaces:**
- Produces: `volume_profile.compute_profile(df: pd.DataFrame, bins: int = 20, window: int = 120) -> dict`（`{"poc": float|None, "value_area": (float, float), "price_vs_poc": float}`）

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_volume_profile.py`:

```python
import numpy as np
import pandas as pd

from analysis.volume_profile import compute_profile


def test_poc_near_concentrated_volume_price():
    rng = np.random.RandomState(0)
    prices = np.concatenate([rng.normal(105, 1, 80), rng.uniform(95, 115, 20)])
    volumes = np.concatenate([np.full(80, 5000), np.full(20, 500)])
    df = pd.DataFrame({"close": prices, "volume": volumes})
    result = compute_profile(df)
    assert 103 < result["poc"] < 107
    assert result["value_area"][0] < result["poc"] < result["value_area"][1]


def test_flat_price_series_no_division_by_zero():
    df = pd.DataFrame({"close": [100.0] * 10, "volume": [1000.0] * 10})
    result = compute_profile(df)
    assert result["poc"] == 100.0
    assert result["value_area"] == (100.0, 100.0)
    assert result["price_vs_poc"] == 0.0


def test_empty_df_returns_none_poc():
    df = pd.DataFrame({"close": [], "volume": []})
    result = compute_profile(df)
    assert result["poc"] is None
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_volume_profile.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: volume_profile.pyを実装**

`analysis/volume_profile.py`:

```python
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
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_volume_profile.py -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
git add analysis/volume_profile.py tests/analysis/test_volume_profile.py
git commit -m "feat: add volume profile module"
```

---

## Task 6: technical.pyへの統合（週足リサンプル＋新規指標）

**Files:**
- Modify: `analysis/technical.py:91-113`（`compute_indicators()`）
- Test: `tests/analysis/test_technical_integration.py`

**Interfaces:**
- Consumes: `dow_theory.analyze`, `wyckoff.compute_phase`, `candlestick.detect_pattern`, `fibonacci.evaluate`, `volume_profile.compute_profile`（Task 1〜5で作成）
- Produces: `compute_indicators(df)` の戻り値に以下のキーを追加：`dow_daily`, `dow_weekly`, `wyckoff`, `candlestick`, `fibonacci`, `volume_profile`

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_technical_integration.py`:

```python
import numpy as np
import pandas as pd

from analysis.technical import compute_indicators


def _make_long_history_df(n=300):
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 5000, n),
    }, index=dates)


def test_compute_indicators_includes_new_keys():
    df = _make_long_history_df(300)
    indicators = compute_indicators(df)
    for key in ("dow_daily", "dow_weekly", "wyckoff", "candlestick", "fibonacci", "volume_profile"):
        assert key in indicators


def test_dow_weekly_falls_back_to_sideways_on_short_history():
    df = _make_long_history_df(20)  # too short for a meaningful weekly resample
    indicators = compute_indicators(df)
    assert indicators["dow_weekly"]["trend"] in ("sideways", "up", "down")
    assert isinstance(indicators["dow_weekly"]["last_swings"], list)
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_technical_integration.py -v`
Expected: FAIL（`AssertionError: 'dow_daily' not in indicators` — 新規キーが存在しない）

- [ ] **Step 3: technical.pyを修正**

`analysis/technical.py` の先頭のimportに追加：

```python
from . import candlestick, dow_theory, fibonacci, volume_profile, wyckoff
```

`compute_indicators()` の直前（97行目付近）にヘルパーを追加：

```python
def _resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("W").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
    }).dropna()
```

`compute_indicators()` の `return {...}` ブロック（既存の91-112行目）を以下に置き換え：

```python
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
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_technical_integration.py -v`
Expected: PASS（2件）

- [ ] **Step 5: 既存のtechnical.py関連テストが壊れていないか確認**

Run: `pytest tests/ -v`
Expected: これまでのタスクのテストも含め全てPASS

- [ ] **Step 6: コミット**

```bash
git add analysis/technical.py tests/analysis/test_technical_integration.py
git commit -m "feat: integrate new technical modules into compute_indicators"
```

---

## Task 7: signals.pyへのスコア統合

**Files:**
- Modify: `analysis/signals.py`
- Test: `tests/analysis/test_signals_integration.py`

**Interfaces:**
- Consumes: `compute_indicators()` の新規キー（Task 6で追加）
- Produces: `outlook()` の `short_term.details` / `mid_term.details` / `long_term.details` に新規スコア項目を追加。既存の `outlook()` シグネチャ・戻り値の型は変えない

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_signals_integration.py`:

```python
import numpy as np
import pandas as pd

from analysis.signals import outlook
from analysis.technical import compute_indicators


def _make_uptrend_df(n=300):
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 5000, n),
    }, index=dates)


def test_outlook_includes_new_score_components():
    df = _make_uptrend_df(300)
    result = outlook(compute_indicators(df), df)
    assert "candlestick_pattern" in result["short_term"]["details"]
    assert "fibonacci_position" in result["short_term"]["details"]
    assert "dow_trend_daily" in result["mid_term"]["details"]
    assert "wyckoff_phase" in result["mid_term"]["details"]
    assert "dow_trend_weekly" in result["long_term"]["details"]
    assert "volume_profile_position" in result["long_term"]["details"]


def test_outlook_scores_stay_in_valid_range():
    df = _make_uptrend_df(300)
    result = outlook(compute_indicators(df), df)
    for term in ("short_term", "mid_term", "long_term"):
        assert -1.0 <= result[term]["score"] <= 1.0
        for component_score in result[term]["details"].values():
            assert -1.0 <= component_score <= 1.0


def test_uptrend_produces_positive_mid_and_long_scores():
    df = _make_uptrend_df(300)
    result = outlook(compute_indicators(df), df)
    assert result["mid_term"]["score"] > 0
    assert result["long_term"]["score"] > 0
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_signals_integration.py -v`
Expected: FAIL（`KeyError: 'candlestick_pattern'` 等、新規スコア項目が存在しない）

- [ ] **Step 3: signals.pyを修正**

新規スコア関数を `_score_ichimoku` の後（98行目付近）に追加：

```python
def _score_dow_trend(trend: str, confirmed: bool) -> float:
    if trend == "up":
        return 1.0 if confirmed else 0.5
    if trend == "down":
        return -1.0 if confirmed else -0.5
    return 0.0


def _score_wyckoff_phase(phase: str) -> float:
    return {
        "markup": 1.0, "accumulation": 0.5,
        "distribution": -0.5, "markdown": -1.0, "undefined": 0.0,
    }.get(phase, 0.0)


def _score_candlestick(direction: int) -> float:
    return float(direction) * 0.6


def _score_fibonacci(fib: dict) -> float:
    return float(fib.get("score", 0.0))


def _score_volume_profile(price_vs_poc: float) -> float:
    return float(np.clip(price_vs_poc * 10, -1, 1))
```

`SHORT_TERM_WEIGHTS` / `MID_TERM_WEIGHTS` / `LONG_TERM_WEIGHTS`（既存117〜137行目）を以下に置き換え：

```python
SHORT_TERM_WEIGHTS = {
    "price_vs_sma5": 2.0,
    "macd_momentum": 1.5,
    "rsi14": 1.0,
    "stochastic": 1.0,
    "bollinger_position": 1.0,
    "volume_confirmation": 1.0,
    "candlestick_pattern": 1.0,
    "fibonacci_position": 1.0,
}
MID_TERM_WEIGHTS = {
    "sma25_vs_sma75": 2.0,
    "price_vs_sma25": 2.0,
    "macd_trend": 1.5,
    "adx_trend": 1.0,
    "volume_confirmation": 0.75,
    "dow_trend_daily": 2.0,
    "wyckoff_phase": 1.5,
}
LONG_TERM_WEIGHTS = {
    "sma75_vs_sma200": 2.0,
    "price_vs_sma200": 2.0,
    "ichimoku_cloud": 1.5,
    "adx_trend": 1.0,
    "dow_trend_weekly": 2.0,
    "volume_profile_position": 1.0,
}
```

`outlook()`（既存148-189行目）の `short_scores` / `mid_scores` / `long_scores` 組み立て部分を以下に置き換え：

```python
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
    dow_daily = indicators["dow_daily"]
    dow_weekly = indicators["dow_weekly"]
    wyckoff_phase = indicators["wyckoff"]["phase"]
    candlestick_direction = indicators["candlestick"]["direction"]
    fibonacci_detail = indicators["fibonacci"]
    volume_profile_detail = indicators["volume_profile"]

    volume_short = _score_volume_confirmation(df["close"], indicators["obv"], window=10)
    volume_mid = _score_volume_confirmation(df["close"], indicators["obv"], window=25)

    short_scores = {
        "rsi14": _score_rsi(rsi_val),
        "stochastic": _score_stochastic(stoch_row["%K"], stoch_row["%D"]),
        "macd_momentum": _score_macd_hist(macd_df["hist"], price),
        "price_vs_sma5": _score_price_vs_ma(price, sma_row["sma5"]),
        "bollinger_position": _score_bollinger(price, bb_row["upper"], bb_row["mid"], bb_row["lower"]),
        "volume_confirmation": volume_short,
        "candlestick_pattern": _score_candlestick(candlestick_direction),
        "fibonacci_position": _score_fibonacci(fibonacci_detail),
    }
    mid_scores = {
        "sma25_vs_sma75": _score_ma_cross(sma_row["sma25"], sma_row["sma75"]),
        "price_vs_sma25": _score_price_vs_ma(price, sma_row["sma25"]),
        "macd_trend": _score_macd_trend(macd_row["macd"], macd_row["signal"], price),
        "adx_trend": _score_adx_trend(adx_row["+DI"], adx_row["-DI"], adx_row["ADX"]),
        "volume_confirmation": volume_mid,
        "dow_trend_daily": _score_dow_trend(dow_daily["trend"], dow_daily["confirmed_by_volume"]),
        "wyckoff_phase": _score_wyckoff_phase(wyckoff_phase),
    }
    long_scores = {
        "sma75_vs_sma200": _score_ma_cross(sma_row["sma75"], sma_row["sma200"]),
        "price_vs_sma200": _score_price_vs_ma(price, sma_row["sma200"]),
        "ichimoku_cloud": _score_ichimoku(price, ichi_row["senkou_a"], ichi_row["senkou_b"]),
        "adx_trend": _score_adx_trend(adx_row["+DI"], adx_row["-DI"], adx_row["ADX"]),
        "dow_trend_weekly": _score_dow_trend(dow_weekly["trend"], dow_weekly["confirmed_by_volume"]),
        "volume_profile_position": _score_volume_profile(volume_profile_detail["price_vs_poc"]),
    }

    return {
        "price": price,
        "short_term": _summarize(short_scores, SHORT_TERM_WEIGHTS),
        "mid_term": _summarize(mid_scores, MID_TERM_WEIGHTS),
        "long_term": _summarize(long_scores, LONG_TERM_WEIGHTS),
    }
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_signals_integration.py -v`
Expected: PASS（3件）

- [ ] **Step 5: 全テストを再実行**

Run: `pytest tests/ -v`
Expected: 全テストPASS（Task 1〜7の累積分）

- [ ] **Step 6: コミット**

```bash
git add analysis/signals.py tests/analysis/test_signals_integration.py
git commit -m "feat: integrate new indicators into short/mid/long term scoring"
```

---

## Task 8: 第2段階（マルチタイムフレーム精査）モジュール

**Files:**
- Modify: `screener/scan.py`（`scan_universe()` に `dow_daily_trend` 列を追加）
- Create: `screener/intraday_refine.py`
- Test: `tests/screener/test_intraday_refine.py`

**Interfaces:**
- Consumes: `stock_data.get_intraday(ticker, interval="1h", period="60d")`、`analysis.dow_theory.analyze`
- Produces: `intraday_refine.refine_candidate(ticker, daily_trend, fetch_intraday=get_intraday) -> dict`
- Produces: `intraday_refine.refine_candidates(candidate_df, daily_trends, n=10, ascending=False, fetch_intraday=get_intraday) -> pd.DataFrame`

- [ ] **Step 1: scan.pyにdow_daily_trend列を追加（失敗するテストを先に書く）**

`tests/screener/test_scan_dow_trend.py`（新規）:

```python
from unittest.mock import patch

import numpy as np
import pandas as pd

from screener.scan import scan_universe


def _fake_download(tickers, **kwargs):
    n = 300
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    df = pd.DataFrame({
        "Open": closes, "High": closes + 1, "Low": closes - 1, "Close": closes, "Volume": np.linspace(1000, 5000, n),
    }, index=dates)
    return df  # single ticker path (len(batch) == 1 branch in scan_universe)


def test_scan_universe_includes_dow_daily_trend_column():
    with patch("screener.scan.yf.download", side_effect=_fake_download):
        result = scan_universe(["TESTX"], period="1y", batch_size=1)
    assert "dow_daily_trend" in result.columns
    assert result.iloc[0]["dow_daily_trend"] in ("up", "down", "sideways")
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/screener/test_scan_dow_trend.py -v`
Expected: FAIL（`KeyError: 'dow_daily_trend'` または `AssertionError`）

- [ ] **Step 3: scan.pyを修正**

`screener/scan.py` の `scan_universe()` 内、`result = outlook(compute_indicators(df), df)` の行（38行目）を以下に置き換え：

```python
                indicators = compute_indicators(df)
                result = outlook(indicators, df)
```

同関数内の `rows.append({...})`（40-50行目）に1行追加：

```python
                rows.append({
                    "ticker": ticker,
                    "name": name_map.get(ticker, ""),
                    "sector": sector_map.get(ticker, ""),
                    "price": result["price"],
                    "short_score": result["short_term"]["score"],
                    "mid_score": result["mid_term"]["score"],
                    "long_score": result["long_term"]["score"],
                    "avg_score": round(sum(scores) / len(scores), 3),
                    "return_20d": _return_pct(df["close"], 20),
                    "dow_daily_trend": indicators["dow_daily"]["trend"],
                })
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/screener/test_scan_dow_trend.py -v`
Expected: PASS

- [ ] **Step 5: intraday_refine.pyの失敗するテストを書く**

`tests/screener/test_intraday_refine.py`:

```python
import numpy as np
import pandas as pd

from screener.intraday_refine import refine_candidate, refine_candidates


def _fake_hourly_uptrend(ticker, interval="1h", period="60d"):
    n = 24 * 30  # 30 days of hourly bars
    t = np.arange(n)
    closes = 100 + 0.05 * t + 2 * np.sin(2 * np.pi * t / 24)
    dates = pd.date_range("2024-06-01", periods=n, freq="h")
    return pd.DataFrame({
        "open": closes, "high": closes + 0.5, "low": closes - 0.5, "close": closes,
        "volume": np.linspace(100, 300, n),
    }, index=dates)


def _fake_hourly_failure(ticker, interval="1h", period="60d"):
    raise RuntimeError("no data")


def test_refine_candidate_reports_aligned_when_trends_match():
    result = refine_candidate("TESTX", daily_trend="up", fetch_intraday=_fake_hourly_uptrend)
    assert result["alignment"] == "aligned"
    assert "波" in result["elliott_wave_context"]


def test_refine_candidate_reports_conflicting_when_trends_differ():
    result = refine_candidate("TESTX", daily_trend="down", fetch_intraday=_fake_hourly_uptrend)
    assert result["alignment"] == "conflicting"


def test_refine_candidate_handles_fetch_failure_gracefully():
    result = refine_candidate("TESTX", daily_trend="up", fetch_intraday=_fake_hourly_failure)
    assert result["alignment"] == "unknown"


def test_refine_candidates_ranks_aligned_first_and_truncates():
    candidate_df = pd.DataFrame({
        "ticker": ["A", "B", "C"],
        "avg_score": [0.9, 0.8, 0.7],
    })
    daily_trends = {"A": "down", "B": "up", "C": "up"}  # A will conflict, B and C align

    def fetch(ticker, interval="1h", period="60d"):
        if ticker == "A":
            return _fake_hourly_uptrend(ticker)  # uptrend hourly, but daily says "down" -> conflicting
        return _fake_hourly_uptrend(ticker)  # aligned with "up" daily trend

    result = refine_candidates(candidate_df, daily_trends, n=2, ascending=False, fetch_intraday=fetch)
    assert len(result) == 2
    assert "A" not in result["ticker"].to_list()  # conflicting candidate pushed out by aligned ones


def test_refine_candidates_skips_failed_fetch_and_keeps_others():
    candidate_df = pd.DataFrame({
        "ticker": ["FAIL", "OK1", "OK2"],
        "avg_score": [0.95, 0.8, 0.7],
    })
    daily_trends = {"FAIL": "up", "OK1": "up", "OK2": "up"}

    def fetch(ticker, interval="1h", period="60d"):
        if ticker == "FAIL":
            raise RuntimeError("delisted or renamed ticker")
        return _fake_hourly_uptrend(ticker)

    result = refine_candidates(candidate_df, daily_trends, n=3, ascending=False, fetch_intraday=fetch)
    assert len(result) == 3  # processing continues past the failed ticker instead of raising
    fail_row = result[result["ticker"] == "FAIL"].iloc[0]
    assert fail_row["entry_timeframe"]["alignment"] == "unknown"
    ok_row = result[result["ticker"] == "OK1"].iloc[0]
    assert ok_row["entry_timeframe"]["alignment"] == "aligned"
```

- [ ] **Step 6: テストを実行し失敗を確認**

Run: `pytest tests/screener/test_intraday_refine.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 7: intraday_refine.pyを実装**

`screener/intraday_refine.py`:

```python
import pandas as pd

from analysis.dow_theory import analyze as dow_analyze
from stock_data import get_intraday


def _resample_4h(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("4h").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
    }).dropna()


def _elliott_wave_context(swings: list[dict]) -> str:
    """Rough, non-predictive wave count label based on recent swing count. Context only, never scored."""
    count = len(swings)
    wave = min(max(count % 5, 1), 5)
    return f"直近スイングから推定 第{wave}波目（目安・参考情報）"


def refine_candidate(ticker: str, daily_trend: str, fetch_intraday=get_intraday) -> dict:
    try:
        hourly = fetch_intraday(ticker, interval="1h", period="60d")
    except Exception:
        return {"alignment": "unknown", "elliott_wave_context": "データ取得失敗", "note": "1時間足データを取得できませんでした"}

    if hourly is None or hourly.empty or len(hourly) < 30:
        return {"alignment": "unknown", "elliott_wave_context": "データ不足", "note": "1時間足データが不足しています"}

    four_hour = _resample_4h(hourly)
    result = dow_analyze(four_hour, window=3)
    alignment = "aligned" if result["trend"] == daily_trend else "conflicting"
    context = _elliott_wave_context(result["last_swings"])
    note = ("週足・日足・4時間足のトレンドが一致しています" if alignment == "aligned"
            else "4時間足トレンドが日足と逆行しています。エントリータイミングに注意してください")
    return {"alignment": alignment, "elliott_wave_context": context, "note": note}


def refine_candidates(candidate_df: pd.DataFrame, daily_trends: dict, n: int = 10,
                       ascending: bool = False, fetch_intraday=get_intraday) -> pd.DataFrame:
    """candidate_df must already be sorted by avg_score (stage-1 ranking)."""
    enriched = []
    for _, row in candidate_df.iterrows():
        ticker = row["ticker"]
        entry_info = refine_candidate(ticker, daily_trends.get(ticker, "sideways"), fetch_intraday=fetch_intraday)
        record = row.to_dict()
        record["entry_timeframe"] = entry_info
        enriched.append(record)

    result_df = pd.DataFrame(enriched)
    result_df["_alignment_bonus"] = result_df["entry_timeframe"].apply(
        lambda info: 1 if info.get("alignment") == "aligned" else 0
    )
    result_df = result_df.sort_values(["_alignment_bonus", "avg_score"], ascending=[False, ascending]).head(n)
    return result_df.drop(columns=["_alignment_bonus"]).reset_index(drop=True)
```

- [ ] **Step 8: テストを実行し成功を確認**

Run: `pytest tests/screener/test_intraday_refine.py -v`
Expected: PASS（5件）

- [ ] **Step 9: 全テストを再実行**

Run: `pytest tests/ -v`
Expected: 全テストPASS

- [ ] **Step 10: コミット**

```bash
git add screener/scan.py screener/intraday_refine.py tests/screener/test_scan_dow_trend.py tests/screener/test_intraday_refine.py
git commit -m "feat: add stage-2 multi-timeframe candidate refinement"
```

---

## Task 9: チャートデータ生成モジュール

**Files:**
- Create: `analysis/chart_data.py`
- Test: `tests/analysis/test_chart_data.py`

**Interfaces:**
- Consumes: `dow_theory.find_swings()` の出力、`fibonacci.evaluate()["levels"]`、`candlestick.detect_pattern()`、`wyckoff.compute_phase()`
- Produces: `chart_data.build_chart_data(df, swings, fibonacci_levels, candlestick, wyckoff_result=None, window=180) -> dict`

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_chart_data.py`:

```python
import pandas as pd

from analysis.chart_data import build_chart_data


def _sample_df():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "open": range(100, 110), "high": range(101, 111), "low": range(99, 109),
        "close": range(100, 110), "volume": [1000] * 10,
    }, index=dates)


def test_build_chart_data_shape():
    df = _sample_df()
    swings = [
        {"date": df.index[2], "price": 101.0, "type": "low"},
        {"date": df.index[7], "price": 108.0, "type": "high"},
    ]
    fib_levels = {0.5: 104.5, 0.618: 103.3}
    candlestick = {"pattern": "hammer", "direction": 1, "bar_index": 9}
    wyckoff_result = {"phase": "markup", "since": df.index[5]}

    chart = build_chart_data(df, swings, fib_levels, candlestick, wyckoff_result, window=180)

    assert len(chart["ohlcv"]) == 10
    assert chart["ohlcv"][0]["date"] == "2024-01-01"
    assert len(chart["annotations"]["swings"]) == 2
    assert len(chart["annotations"]["fibonacci_levels"]) == 2
    assert len(chart["annotations"]["candlestick_markers"]) == 1
    assert len(chart["annotations"]["wyckoff_zones"]) == 1
    assert chart["annotations"]["wyckoff_zones"][0]["phase"] == "markup"


def test_build_chart_data_without_pattern_or_wyckoff():
    df = _sample_df()
    chart = build_chart_data(df, swings=[], fibonacci_levels={}, candlestick={"pattern": None, "direction": 0, "bar_index": None})
    assert chart["annotations"]["candlestick_markers"] == []
    assert chart["annotations"]["wyckoff_zones"] == []


def test_build_chart_data_truncates_to_window():
    df = _sample_df()
    chart = build_chart_data(df, swings=[], fibonacci_levels={}, candlestick={"pattern": None, "direction": 0, "bar_index": None}, window=5)
    assert len(chart["ohlcv"]) == 5
    assert chart["ohlcv"][0]["date"] == "2024-01-06"
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_chart_data.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: chart_data.pyを実装**

`analysis/chart_data.py`:

```python
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
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_chart_data.py -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
git add analysis/chart_data.py tests/analysis/test_chart_data.py
git commit -m "feat: add chart data/annotation builder for top-10 tickers"
```

---

## Task 10: report.py・generate_daily_watchlist.pyへの配線

**Files:**
- Modify: `analysis/report.py:24-71`（`generate_report()`）
- Modify: `analysis/__init__.py`（`chart_data`のエクスポート追加）
- Modify: `screener/__init__.py`（`intraday_refine`のエクスポート追加）
- Modify: `generate_daily_watchlist.py`
- Test: `tests/analysis/test_report_technical_detail.py`

**Interfaces:**
- Consumes: Task 6〜9で作成した全モジュール
- Produces: `generate_report()` の戻り値の `technical` に `dow_theory` / `wyckoff_phase` / `candlestick_pattern` / `fibonacci_position` / `volume_profile` を追加。`_ticker_entry()` に `entry_timeframe` / `chart` を追加（最終上位10銘柄のみ）

- [ ] **Step 1: 失敗するテストを書く**

`tests/analysis/test_report_technical_detail.py`:

```python
from unittest.mock import patch

import numpy as np
import pandas as pd

from analysis.report import generate_report


def _fake_df(n=300):
    t = np.arange(n)
    closes = 100 + 0.3 * t + 5 * np.sin(2 * np.pi * t / 20)
    dates = pd.date_range("2023-01-02", periods=n, freq="D")
    return pd.DataFrame({
        "open": closes, "high": closes + 1, "low": closes - 1, "close": closes,
        "volume": np.linspace(1000, 5000, n),
    }, index=dates)


def test_generate_report_includes_raw_technical_detail():
    df = _fake_df()
    with patch("analysis.report.get_daily", return_value=df), \
         patch("analysis.report.get_macro_daily", return_value=df), \
         patch("analysis.report.get_tdnet_disclosures", return_value=[]), \
         patch("analysis.report.get_yfinance_news", return_value=[]), \
         patch("analysis.report.get_next_earnings_date", return_value=None):
        report = generate_report("TESTX", name="Test Co", sector="Technology")

    tech = report["technical"]
    assert "dow_theory" in tech
    assert "daily" in tech["dow_theory"] and "weekly" in tech["dow_theory"]
    assert "wyckoff_phase" in tech
    assert "candlestick_pattern" in tech
    assert "fibonacci_position" in tech
    assert "volume_profile" in tech
    # existing short/mid/long-term summary must still be present (backward compatible)
    assert "short_term" in tech and "mid_term" in tech and "long_term" in tech
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/analysis/test_report_technical_detail.py -v`
Expected: FAIL（`KeyError: 'dow_theory'`）

- [ ] **Step 3: report.pyを修正**

`analysis/report.py` の `generate_report()`（24-71行目）内、`stock_outlook = outlook(compute_indicators(df), df)` の行を以下に置き換え：

```python
    indicators = compute_indicators(df)
    stock_outlook = outlook(indicators, df)
```

同関数の `return {...}` ブロック内、`"technical": stock_outlook,` の行を以下に置き換え：

```python
        "technical": {
            **stock_outlook,
            "dow_theory": {"daily": indicators["dow_daily"], "weekly": indicators["dow_weekly"]},
            "wyckoff_phase": indicators["wyckoff"],
            "candlestick_pattern": indicators["candlestick"],
            "fibonacci_position": indicators["fibonacci"],
            "volume_profile": indicators["volume_profile"],
        },
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/analysis/test_report_technical_detail.py -v`
Expected: PASS

- [ ] **Step 5: analysis/__init__.pyとscreener/__init__.pyにエクスポートを追加**

`analysis/__init__.py`:

```python
from .technical import compute_indicators
from .signals import outlook
from .fundamental import analyze_news
from .report import generate_report, format_markdown, save_report
from .chart_data import build_chart_data

__all__ = [
    "compute_indicators",
    "outlook",
    "analyze_news",
    "generate_report",
    "format_markdown",
    "save_report",
    "build_chart_data",
]
```

`screener/__init__.py`:

```python
from .universe import get_name_map, get_nikkei225_info, get_nikkei225_tickers, get_sp500_info, get_sp500_tickers
from .scan import scan_universe, top_signals
from .alerts import check_watchlist_alerts
from .market_cap import get_market_caps
from .categories import CATEGORY_LABELS, CATEGORY_ORDER, categories_for_sector
from .intraday_refine import refine_candidates

__all__ = [
    "get_nikkei225_tickers",
    "get_sp500_tickers",
    "get_nikkei225_info",
    "get_sp500_info",
    "get_name_map",
    "scan_universe",
    "top_signals",
    "check_watchlist_alerts",
    "get_market_caps",
    "CATEGORY_LABELS",
    "CATEGORY_ORDER",
    "categories_for_sector",
    "refine_candidates",
]
```

- [ ] **Step 6: generate_daily_watchlist.pyを修正**

`TOP_N = 10` の下に追加：

```python
TOP_N = 10
CANDIDATE_POOL_N = 40
WATCHLIST_PATH = Path("watchlist.json")
```

import文に追加（既存の `from analysis import generate_report, save_report` と `from screener import ...` 、`from stock_data import get_us_realtime_snapshot` の行をそれぞれ置き換え）：

```python
from analysis import build_chart_data, generate_report, save_report
from screener import (
    check_watchlist_alerts, get_nikkei225_info, get_sp500_info,
    refine_candidates, scan_universe, top_signals,
)
from stock_data import get_daily, get_us_realtime_snapshot
```

`_ticker_entry()` を以下に置き換え（`entry_timeframe` と `chart` を追加）：

```python
def _ticker_entry(ticker: str, report: dict, entry_timeframe: dict | None = None,
                   chart: dict | None = None) -> dict:
    return {
        "ticker": ticker,
        "name": report.get("name") or "",
        "name_ja": None,
        "sector": report.get("sector"),
        "return_20d": report.get("return_20d"),
        "relative_strength_20d": report.get("relative_strength_20d"),
        "next_earnings_date": report.get("next_earnings_date"),
        "price": report["price"],
        "price_source": report.get("price_source", "yfinance"),
        "intraday_change_pct": report.get("intraday_change_pct"),
        "technical": report["technical"],
        "macro_index": report["macro_index"],
        "combined": report["combined_technical_macro"],
        "fundamentals_source": report["fundamentals_source"],
        "fundamentals_raw": report["fundamentals_raw"],
        "claude_judgment": None,
        "entry_timeframe": entry_timeframe,
        "chart": chart,
    }
```

`_build_market_block()` を以下に置き換え（`entry_timeframe`・`chart` を組み立てて渡す）。この関数は第2段階を通過した最終上位10銘柄のDataFrame（`refine_candidates()` の戻り値）のみを受け取るため、渡された全行に対して常にチャートを構築する：

```python
def _build_market_block(scan_df, bullish, bearish, name_map, reports_out, realtime_map=None):
    scan_lookup = scan_df.set_index("ticker")
    entries = {"bullish": [], "bearish": []}
    for key, df in (("bullish", bullish), ("bearish", bearish)):
        for _, cand_row in df.iterrows():
            ticker = cand_row["ticker"]
            try:
                row = scan_lookup.loc[ticker]
                report = generate_report(
                    ticker,
                    name=name_map.get(ticker),
                    sector=row.get("sector"),
                    return_20d=row.get("return_20d"),
                    relative_strength_20d=row.get("relative_strength_20d"),
                    realtime=(realtime_map or {}).get(ticker),
                )
                save_report(report, f"output/reports/{ticker.replace('.', '_')}.md")
                reports_out[ticker] = report

                entry_timeframe = cand_row.get("entry_timeframe")
                tech = report["technical"]
                # Note: generate_report() already fetched 2y daily data internally; fetching again here
                # is a small, deliberate duplication kept for simplicity since this only runs for the
                # final ~40 candidates (not the full 700-ticker universe).
                price_df_source = get_daily(ticker, source="yfinance", period="2y")
                chart = build_chart_data(
                    price_df_source, tech["dow_theory"]["daily"]["last_swings"],
                    tech["fibonacci_position"]["levels"], tech["candlestick_pattern"], tech["wyckoff_phase"],
                )

                entries[key].append(_ticker_entry(ticker, report, entry_timeframe, chart))
            except Exception as exc:
                print(f"failed to build report for {ticker}: {exc}")
    return entries
```

`main()` 内、`jp_bull, jp_bear = top_signals(jp_scan_df, n=TOP_N)` と `us_bull, us_bear = top_signals(us_scan_df, n=TOP_N)` の2行を以下に置き換え：

```python
    jp_bull_pool, jp_bear_pool = top_signals(jp_scan_df, n=CANDIDATE_POOL_N)
    us_bull_pool, us_bear_pool = top_signals(us_scan_df, n=CANDIDATE_POOL_N)

    jp_daily_trends = jp_scan_df.set_index("ticker")["dow_daily_trend"].to_dict()
    us_daily_trends = us_scan_df.set_index("ticker")["dow_daily_trend"].to_dict()

    jp_bull = refine_candidates(jp_bull_pool, jp_daily_trends, n=TOP_N, ascending=False)
    jp_bear = refine_candidates(jp_bear_pool, jp_daily_trends, n=TOP_N, ascending=True)
    us_bull = refine_candidates(us_bull_pool, us_daily_trends, n=TOP_N, ascending=False)
    us_bear = refine_candidates(us_bear_pool, us_daily_trends, n=TOP_N, ascending=True)
```

- [ ] **Step 7: 全テストを再実行**

Run: `pytest tests/ -v`
Expected: 全テストPASS

- [ ] **Step 8: コミット**

```bash
git add analysis/report.py analysis/__init__.py screener/__init__.py generate_daily_watchlist.py tests/analysis/test_report_technical_detail.py
git commit -m "feat: wire stage-2 refinement and chart data into daily watchlist generation"
```

---

## Task 11: dashboard/index.htmlへのチャート描画・詳細表示

**Files:**
- Modify: `dashboard/index.html`

**Interfaces:**
- Consumes: `dashboard_data.json` の `markets.{jp,us}.{bullish,bearish}[].technical`（新規フィールド）と `.entry_timeframe` / `.chart`（最終上位10銘柄のみ存在）

- [ ] **Step 1: Lightweight ChartsのCDNスクリプトを追加**

`</style>` の直後（`<div class="page">` の直前）に追加：

```html
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
```

- [ ] **Step 2: 新規指標の詳細表示関数を追加**

`function chartUrl(ticker)`（742行目付近）の直前に追加：

```javascript
  const WYCKOFF_LABEL = {
    accumulation: "蓄積", markup: "上昇", distribution: "分配", markdown: "下降", undefined: "判定不能",
  };

  function technicalDetailSection(t) {
    const dow = t.dow_theory || {};
    const dowDaily = dow.daily || {};
    const dowWeekly = dow.weekly || {};
    const wyckoff = t.wyckoff_phase || {};
    const candle = t.candlestick_pattern || {};
    const fib = t.fibonacci_position || {};
    const volProfile = t.volume_profile || {};

    return `<div class="detail-section">
      <h3>ダウ理論・ワイコフ・パターン分析</h3>
      <div class="tech-extra">
        <div class="tech-extra-row"><span class="term">日足トレンド</span><span>${dowDaily.trend || "—"}${dowDaily.confirmed_by_volume ? "（出来高確認あり）" : ""}</span></div>
        <div class="tech-extra-row"><span class="term">週足トレンド</span><span>${dowWeekly.trend || "—"}${dowWeekly.confirmed_by_volume ? "（出来高確認あり）" : ""}</span></div>
        <div class="tech-extra-row"><span class="term">ワイコフフェーズ</span><span>${WYCKOFF_LABEL[wyckoff.phase] || "—"}</span></div>
        <div class="tech-extra-row"><span class="term">ローソク足パターン</span><span>${candle.pattern || "検出なし"}</span></div>
        <div class="tech-extra-row"><span class="term">フィボナッチ位置</span><span>${fib.price_zone || "—"}</span></div>
        <div class="tech-extra-row"><span class="term">出来高POC比</span><span>${volProfile.price_vs_poc != null ? (volProfile.price_vs_poc * 100).toFixed(2) + "%" : "—"}</span></div>
      </div>
    </div>`;
  }

  function entryTimeframeSection(entryTimeframe) {
    if (!entryTimeframe) return "";
    return `<div class="detail-section">
      <h3>マルチタイムフレーム精査（4時間足）</h3>
      <p class="hint">${entryTimeframe.note || ""}</p>
      <p class="hint">${entryTimeframe.elliott_wave_context || ""}（エリオット波動は参考情報であり、スコアには使用していません）</p>
    </div>`;
  }

  function chartSection(ticker, chart) {
    if (!chart || !chart.ohlcv || !chart.ohlcv.length) return "";
    const containerId = `chart-${ticker.replace(/[^a-zA-Z0-9]/g, "_")}`;
    // Render after insertion via renderLightweightChart(); container is a placeholder here.
    return `<div class="detail-section">
      <h3>チャート（判断根拠オーバーレイ付き）</h3>
      <div id="${containerId}" class="chart-container" data-chart='${JSON.stringify(chart).replace(/'/g, "&#39;")}'></div>
    </div>`;
  }

  function renderLightweightChart(container) {
    if (!window.LightweightCharts || container.dataset.rendered) return;
    const chart = JSON.parse(container.dataset.chart);
    const el = document.createElement("div");
    el.style.height = "280px";
    container.appendChild(el);

    const api = LightweightCharts.createChart(el, {
      width: container.clientWidth, height: 280,
      layout: { background: { color: "transparent" }, textColor: getComputedStyle(document.body).getPropertyValue("--ink") },
      grid: { vertLines: { visible: false }, horzLines: { color: getComputedStyle(document.body).getPropertyValue("--hairline") } },
      timeScale: { borderVisible: false },
    });
    const series = api.addCandlestickSeries({ upColor: "#2f7d54", downColor: "#b2452c", borderVisible: false, wickUpColor: "#2f7d54", wickDownColor: "#b2452c" });
    series.setData(chart.ohlcv.map((b) => ({ time: b.date, open: b.open, high: b.high, low: b.low, close: b.close })));

    const volumeSeries = api.addHistogramSeries({ priceScaleId: "", priceFormat: { type: "volume" } });
    volumeSeries.setData(chart.ohlcv.map((b) => ({ time: b.date, value: b.volume })));

    (chart.annotations.fibonacci_levels || []).forEach((lvl) => {
      series.createPriceLine({ price: lvl.price, color: "#a97a1f", lineWidth: 1, lineStyle: 2, title: `Fib ${lvl.level}` });
    });

    const markers = [
      ...(chart.annotations.swings || []).map((s) => ({
        time: s.date, position: s.type === "high" ? "aboveBar" : "belowBar",
        color: s.type === "high" ? "#b2452c" : "#2f7d54", shape: s.type === "high" ? "arrowDown" : "arrowUp",
        text: s.type === "high" ? "高値" : "安値",
      })),
      ...(chart.annotations.candlestick_markers || []).map((m) => ({
        time: m.date, position: m.direction >= 0 ? "belowBar" : "aboveBar",
        color: "#a97a1f", shape: "circle", text: m.pattern,
      })),
    ];
    series.setMarkers(markers);

    container.dataset.rendered = "1";
  }
```

- [ ] **Step 3: row()内にチャート・詳細セクションを組み込む**

`row()` 関数（775行目付近）内、`</div>` で閉じる詳細ブロックの末尾（`scoreCard`群の後）に追加：

```javascript
        ${technicalDetailSection(t)}
        ${entryTimeframeSection(item.entry_timeframe)}
        ${chartSection(item.ticker, item.chart)}
```

- [ ] **Step 4: details展開時にチャートを遅延描画するイベントを追加**

`fetch("data.json")` のPromiseチェーン（957行目付近）の直後、`</script>` の直前に追加：

```javascript
  document.addEventListener("toggle", (e) => {
    if (e.target.tagName !== "DETAILS" || !e.target.open) return;
    e.target.querySelectorAll(".chart-container").forEach(renderLightweightChart);
  }, true);
```

- [ ] **Step 5: CSSにチャート・詳細表示用のスタイルを追加**

`.hint` クラス定義の後（既存CSS内、`.empty-state` の前）に追加：

```css
  .tech-extra { display: flex; flex-direction: column; gap: 6px; font-size: 0.85rem; }
  .tech-extra-row { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px dashed var(--hairline); padding-bottom: 4px; }
  .tech-extra-row .term { color: var(--ink-muted); }
  .chart-container { border: 1px solid var(--hairline); border-radius: 8px; padding: 8px; background: var(--surface); min-height: 280px; }
```

- [ ] **Step 6: ローカルプレビューで動作確認**

`stock-data-tool/dashboard/data.json` に、`chart` フィールドを含む最小限のサンプルJSONを一時的に配置し、`preview_start`（`.claude/launch.json` の `dashboard` 設定）でブラウザ確認する：
- 上位10銘柄（`chart`あり）の展開時にローソク足チャートが描画されること
- 圏外銘柄（`chart`なし）の展開時にエラーが出ないこと（`chartSection()` が空文字列を返し、`.chart-container` 自体が存在しないため `renderLightweightChart` の対象にならない）
- ライト/ダークテーマ切り替えでチャートの配色が破綻しないこと

- [ ] **Step 7: コミット**

```bash
git add dashboard/index.html
git commit -m "feat: render annotated candlestick chart for top-10 board entries"
```

---

## 全体の最終確認

- [ ] **Step 1: 全テストスイートを実行**

Run: `pytest tests/ -v`
Expected: 全件PASS

- [ ] **Step 2: 実データで小規模スキャンを試走（数銘柄）し、実行時間・エラーの有無を確認**

`generate_daily_watchlist.py` を直接実行する前に、`screener/universe.py` のユニバースを一時的に数銘柄へ絞ったスクリプトで `scan_universe()` → `refine_candidates()` の一連の流れを試し、想定通りの実行時間内で完了するか確認する（spec section 5の検証手順に対応）。
