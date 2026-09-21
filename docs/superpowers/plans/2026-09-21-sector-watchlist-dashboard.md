# セクター・ウォッチリストボード Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 宇宙・防衛・船舶・メモリ半導体の4セクター、日米合計30ユニーク銘柄を対象にした固定ウォッチリストの専用ダッシュボードを新設し、毎日1回自動更新する。

**Architecture:** `generate_sector_watchlist.py`（新規）が既存の`analysis.generate_report()`をそのまま呼び出して固定銘柄リストを分析し、`dashboard/sector_watchlist_data.json`に直接書き出す。`dashboard/sector-watchlist.html`（新規）が相場ボードと同じ見た目・コンポーネント（ゲージアニメーション・見立て文・moomooチャートリンク）でこれを表示する。Claude Codeのスケジュールタスクが毎日スクリプトを起動する。

**Tech Stack:** Python 3.12 / pandas（既存の`analysis`パッケージ経由）、pytest、バニラJS/CSS（既存ダッシュボード群と同じ単一HTMLファイル方式）

**Spec:** [docs/superpowers/specs/2026-09-21-sector-watchlist-dashboard-design.md](../specs/2026-09-21-sector-watchlist-dashboard-design.md)

## Global Constraints

- 新規のスコアリングロジックは追加しない。既存の`analysis.generate_report()`をそのまま利用する
- Claude APIによる追加の判断コメント生成は行わない（追加課金を避けるため、ユーザーが明示的に見送りを選択）
- 複数セクターに属する銘柄（7011.T, 7013.T）は、レポート取得は1回のみ行い、表示側で該当する全セクションに複製する
- 出力は`dashboard/sector_watchlist_data.json`に直接書き出す（相場ボード等の手動コピー運用とは異なる）
- 全ての作業は`stock-data-tool/`ディレクトリを起点に行う

## Review Focus

- 個別銘柄のレポート取得に失敗しても、その銘柄をスキップして残りの処理を継続すること（yfinanceの一時的な取得失敗等）
- 複数セクターに属する銘柄がAPI呼び出し側では重複取得されず、表示側では正しく両方のセクションに現れること
- `technical`配下の一部フィールド（`dow_theory`・`wyckoff_phase`等）が欠落していてもJS側が例外を出さないこと（`|| {}`の防御的フォールバックを各所に入れる。このボードは`chart`/`entry_timeframe`フィールド自体を持たない設計のため、それらは該当なし）
- JSON書き出し時にNaN等の非JSON準拠値が混入して書き込み自体が失敗しないこと（`_sanitize()`の既存パターンを踏襲）
- 空の`fundamentals_raw`（ニュース・開示情報が0件）の銘柄で見出し一覧が壊れずに「材料なし」表示になること

---

## Task 1: 銘柄リスト・重複排除・エントリー整形ロジック

**Files:**
- Create: `generate_sector_watchlist.py`（このタスクではモジュール定数と純粋関数のみ実装。`main()`はTask 2）
- Test: `tests/test_generate_sector_watchlist.py`

**Interfaces:**
- Produces: `SECTOR_TICKERS: dict[str, dict[str, list[str]]]`（セクター名 → 市場（"us"/"jp"） → ティッカーリスト）
- Produces: `dedupe_tickers(sector_tickers: dict) -> list[dict]`（`[{"ticker": str, "market": "us"|"jp"}, ...]`、ユニーク）
- Produces: `build_sector_payload(sector_tickers: dict, reports_by_ticker: dict) -> list[dict]`（`[{"name": str, "us": [entry, ...], "jp": [entry, ...]}, ...]`）
- Produces: `_build_entry(ticker: str, report: dict) -> dict`
- Produces: `_sanitize(obj)`（`generate_daily_watchlist.py`と同じNaN/Inf処理）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_generate_sector_watchlist.py`:

```python
import math

from generate_sector_watchlist import (
    SECTOR_TICKERS,
    _build_entry,
    _sanitize,
    build_sector_payload,
    dedupe_tickers,
)


def test_sector_tickers_covers_four_sectors_with_four_each():
    assert set(SECTOR_TICKERS.keys()) == {"宇宙", "防衛", "船舶", "メモリ半導体"}
    for sector, markets in SECTOR_TICKERS.items():
        assert len(markets["us"]) == 4, sector
        assert len(markets["jp"]) == 4, sector


def test_dedupe_tickers_removes_cross_sector_duplicates():
    sector_tickers = {
        "宇宙": {"us": ["SPCX"], "jp": ["7011.T"]},
        "防衛": {"us": ["LMT"], "jp": ["7011.T"]},
    }
    result = dedupe_tickers(sector_tickers)
    result_set = {(r["ticker"], r["market"]) for r in result}
    assert result_set == {("SPCX", "us"), ("7011.T", "jp"), ("LMT", "us")}
    assert len(result) == 3  # 7011.T counted once despite appearing in two sectors


def test_build_entry_shapes_report_for_dashboard():
    report = {
        "ticker": "7011.T", "name": "三菱重工業", "price": 3879.0, "price_source": "yfinance",
        "technical": {"short_term": {"score": 0.28, "label": "やや強気"}},
        "fundamentals_source": "TDnet",
        "fundamentals_raw": [{"title": "決算発表", "published_at": "2026-09-01"}],
    }
    entry = _build_entry("7011.T", report)
    assert entry["ticker"] == "7011.T"
    assert entry["name"] == "三菱重工業"
    assert entry["price"] == 3879.0
    assert entry["technical"] == report["technical"]
    assert entry["fundamentals_raw"] == report["fundamentals_raw"]


def test_build_sector_payload_duplicates_multi_sector_ticker():
    sector_tickers = {
        "宇宙": {"us": [], "jp": ["7011.T"]},
        "防衛": {"us": [], "jp": ["7011.T"]},
    }
    report = {
        "ticker": "7011.T", "name": "三菱重工業", "price": 3879.0, "price_source": "yfinance",
        "technical": {}, "fundamentals_source": "TDnet", "fundamentals_raw": [],
    }
    reports_by_ticker = {"7011.T": report}
    payload = build_sector_payload(sector_tickers, reports_by_ticker)
    assert len(payload) == 2
    assert payload[0]["name"] == "宇宙"
    assert payload[0]["jp"][0]["ticker"] == "7011.T"
    assert payload[1]["name"] == "防衛"
    assert payload[1]["jp"][0]["ticker"] == "7011.T"
    assert payload[0]["us"] == []


def test_build_sector_payload_skips_ticker_missing_from_reports():
    # a ticker whose report fetch failed (Task 2's error handling) is simply
    # absent from reports_by_ticker; the payload must omit it, not crash
    sector_tickers = {"宇宙": {"us": ["SPCX"], "jp": []}}
    payload = build_sector_payload(sector_tickers, reports_by_ticker={})
    assert payload[0]["us"] == []


def test_sanitize_converts_nan_and_inf_to_none():
    assert _sanitize(float("nan")) is None
    assert _sanitize(float("inf")) is None
    assert _sanitize({"a": [1.0, float("nan")], "b": (2.0, float("inf"))}) == {"a": [1.0, None], "b": [2.0, None]}
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/test_generate_sector_watchlist.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'generate_sector_watchlist'`）

- [ ] **Step 3: generate_sector_watchlist.pyの定数・純粋関数部分を実装**

`generate_sector_watchlist.py`（ファイル冒頭〜純粋関数まで。`main()`はTask 2で追記する）:

```python
SECTOR_TICKERS: dict[str, dict[str, list[str]]] = {
    "宇宙": {
        "us": ["SPCX", "RKLB", "ASTS", "LUNR"],
        "jp": ["9348.T", "7013.T", "7011.T", "464A.T"],
    },
    "防衛": {
        "us": ["LMT", "RTX", "NOC", "GD"],
        "jp": ["7011.T", "7012.T", "7013.T", "5631.T"],
    },
    "船舶": {
        "us": ["ZIM", "FRO", "GOGL", "GNK"],
        "jp": ["9101.T", "9104.T", "9107.T", "7003.T"],
    },
    "メモリ半導体": {
        "us": ["MU", "WDC", "SNDK", "STX"],
        "jp": ["285A.T", "8035.T", "6857.T", "6146.T"],
    },
}

NAME_MAP: dict[str, str] = {
    "SPCX": "SpaceX", "RKLB": "Rocket Lab", "ASTS": "AST SpaceMobile", "LUNR": "Intuitive Machines",
    "LMT": "Lockheed Martin", "RTX": "RTX Corporation", "NOC": "Northrop Grumman", "GD": "General Dynamics",
    "ZIM": "Zim Integrated Shipping", "FRO": "Frontline", "GOGL": "Golden Ocean Group", "GNK": "Genco Shipping",
    "MU": "Micron Technology", "WDC": "Western Digital", "SNDK": "SanDisk", "STX": "Seagate Technology",
    "9348.T": "ispace", "7013.T": "IHI", "7011.T": "三菱重工業", "464A.T": "QPSホールディングス",
    "7012.T": "川崎重工業", "5631.T": "日本製鋼所",
    "9101.T": "日本郵船", "9104.T": "商船三井", "9107.T": "川崎汽船", "7003.T": "三井E&S",
    "285A.T": "キオクシアHD", "8035.T": "東京エレクトロン", "6857.T": "アドバンテスト", "6146.T": "ディスコ",
}


def dedupe_tickers(sector_tickers: dict) -> list[dict]:
    seen: set[str] = set()
    result = []
    for markets in sector_tickers.values():
        for market, tickers in markets.items():
            for ticker in tickers:
                if ticker in seen:
                    continue
                seen.add(ticker)
                result.append({"ticker": ticker, "market": market})
    return result


def _build_entry(ticker: str, report: dict) -> dict:
    return {
        "ticker": ticker,
        "name": report.get("name") or "",
        "name_ja": None,
        "price": report["price"],
        "price_source": report.get("price_source", "yfinance"),
        "technical": report["technical"],
        "fundamentals_source": report.get("fundamentals_source"),
        "fundamentals_raw": report.get("fundamentals_raw") or [],
    }


def build_sector_payload(sector_tickers: dict, reports_by_ticker: dict) -> list[dict]:
    payload = []
    for sector, markets in sector_tickers.items():
        section = {"name": sector}
        for market, tickers in markets.items():
            section[market] = [
                _build_entry(ticker, reports_by_ticker[ticker])
                for ticker in tickers
                if ticker in reports_by_ticker
            ]
        payload.append(section)
    return payload


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj
```

Add `import math` at the top of the file (needed by `_sanitize`).

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/test_generate_sector_watchlist.py -v`
Expected: PASS（6件全て）

- [ ] **Step 5: コミット**

```bash
git add generate_sector_watchlist.py tests/test_generate_sector_watchlist.py
git commit -m "feat: add sector watchlist ticker list and payload-building logic"
```

---

## Task 2: main()オーケストレーションとJSON書き出し

**Files:**
- Modify: `generate_sector_watchlist.py`（Task 1のファイル末尾に追記）
- Test: `tests/test_generate_sector_watchlist.py`（Task 1のファイルに追記）

**Interfaces:**
- Consumes: Task 1の`SECTOR_TICKERS`, `NAME_MAP`, `dedupe_tickers()`, `build_sector_payload()`, `_sanitize()`
- Consumes: `analysis.generate_report(ticker, name=None) -> dict`（既存関数、シグネチャは`analysis/report.py`を参照）
- Produces: `main()` — `dashboard/sector_watchlist_data.json`を書き出す。副作用のためテストは`generate_report`をモックして検証する

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_generate_sector_watchlist.py`に追記:

```python
import json
from pathlib import Path
from unittest.mock import patch


def _fake_report(ticker, name=None, **kwargs):
    if ticker == "FAIL_ME":
        raise RuntimeError("network error")
    return {
        "ticker": ticker, "name": name or ticker, "price": 100.0, "price_source": "yfinance",
        "technical": {"short_term": {"score": 0.1, "label": "中立"}},
        "fundamentals_source": "TDnet", "fundamentals_raw": [],
    }


def test_main_writes_dashboard_json(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    small_sectors = {"宇宙": {"us": ["SPCX"], "jp": ["7011.T"]}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        mod.main()

    out_path = tmp_path / "dashboard" / "sector_watchlist_data.json"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "generated_at" in data
    assert data["sectors"][0]["name"] == "宇宙"
    assert data["sectors"][0]["us"][0]["ticker"] == "SPCX"
    assert data["sectors"][0]["jp"][0]["ticker"] == "7011.T"


def test_main_skips_failing_ticker_and_continues(tmp_path, monkeypatch):
    import generate_sector_watchlist as mod

    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    small_sectors = {"宇宙": {"us": ["SPCX", "FAIL_ME"], "jp": []}}
    with patch.object(mod, "SECTOR_TICKERS", small_sectors), \
         patch.object(mod, "generate_report", side_effect=_fake_report):
        mod.main()

    data = json.loads((tmp_path / "dashboard" / "sector_watchlist_data.json").read_text(encoding="utf-8"))
    tickers = [e["ticker"] for e in data["sectors"][0]["us"]]
    assert tickers == ["SPCX"]  # FAIL_ME skipped, SPCX still present
```

- [ ] **Step 2: テストを実行し失敗を確認**

Run: `pytest tests/test_generate_sector_watchlist.py -k main -v`
Expected: FAIL（`AttributeError: module 'generate_sector_watchlist' has no attribute 'main'`）

- [ ] **Step 3: main()を実装**

`generate_sector_watchlist.py`の先頭に追加のimport:

```python
import json
import math
from datetime import datetime
from pathlib import Path

from analysis import generate_report
```

（`import math`は既にTask 1で追加済みなら重複させない）

ファイル末尾に追記:

```python
def main():
    tickers = dedupe_tickers(SECTOR_TICKERS)
    reports_by_ticker = {}
    for item in tickers:
        ticker = item["ticker"]
        try:
            reports_by_ticker[ticker] = generate_report(ticker, name=NAME_MAP.get(ticker))
        except Exception as exc:
            print(f"failed to build report for {ticker}: {exc}")

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sectors": build_sector_payload(SECTOR_TICKERS, reports_by_ticker),
    }

    out_path = Path("dashboard/sector_watchlist_data.json")
    out_path.write_text(
        json.dumps(_sanitize(payload), ensure_ascii=False, indent=2, default=str, allow_nan=False),
        encoding="utf-8",
    )
    print(f"wrote {out_path} ({len(reports_by_ticker)}/{len(tickers)} tickers)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストを実行し成功を確認**

Run: `pytest tests/test_generate_sector_watchlist.py -v`
Expected: PASS（8件全て）

- [ ] **Step 5: コミット**

```bash
git add generate_sector_watchlist.py tests/test_generate_sector_watchlist.py
git commit -m "feat: add main() orchestration for sector watchlist generation"
```

---

## Task 3: ダッシュボードページ `dashboard/sector-watchlist.html`

**Files:**
- Create: `dashboard/sector-watchlist.html`

**Interfaces:**
- Consumes: `dashboard/sector_watchlist_data.json`（Task 2の出力。`{generated_at, sectors: [{name, us: [entry,...], jp: [entry,...]}, ...]}`、各`entry`は`{ticker, name, name_ja, price, price_source, technical, fundamentals_source, fundamentals_raw}`）

このタスクに自動テストはない（プロジェクトの既存ダッシュボード群と同じくJSテストフレームワークがないため）。ローカルでブラウザ確認する。

- [ ] **Step 1: index.htmlから再利用するパターンを確認する**

`dashboard/index.html`を読み、以下の実装を参照する（コピー元）:
- CSS変数定義（`:root`、ダークモード分岐）— `--bg`, `--surface`, `--ink`, `--bull`, `--bear`, `--accent`, `--hairline`等
- `.gauge` / `.gauge-track` / `.gauge-fill`（アニメーション込み）のCSS
- `.insight-line`, `.tech-extra`, `.tech-extra-row`のCSS
- `fmtNum()`, `escapeAttr()`, `companyName()`, `gauge()`, `animateGauges()`, `scoreCard()`, `WYCKOFF_LABEL`, `TREND_PHRASE`, `WYCKOFF_PHRASE`, `PATTERN_PHRASE`, `insightLine()`, `technicalDetailSection()`のJS実装
- `chartUrl(ticker)`（moomoo証券へのリンク生成、`analysis/report.py`ではなく`dashboard/index.html`内のJS関数）

- [ ] **Step 2: dashboard/sector-watchlist.htmlを作成**

`dashboard/sector-watchlist.html`:

```html
<meta charset="UTF-8">
<title>セクター・ウォッチリストボード</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Old+Mincho:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #f5f1e8;
    --surface: #ffffff;
    --surface-2: #efe8d8;
    --ink: #1d1a15;
    --ink-muted: #746b58;
    --ink-faint: #9a9280;
    --hairline: #e2d9c4;
    --accent: #a97a1f;
    --accent-ink: #ffffff;
    --bull: #2f7d54;
    --bull-soft: #d9ecdf;
    --bear: #b2452c;
    --bear-soft: #f3ddd4;
    --neutral: #8a8270;
    --neutral-soft: #ece6d6;
    --shadow: 0 1px 2px rgba(30, 24, 10, 0.06), 0 8px 24px -16px rgba(30, 24, 10, 0.35);
    --font-display: "Zen Old Mincho", "Hiragino Mincho ProN", serif;
    --font-body: "Zen Kaku Gothic New", "Hiragino Sans", "Noto Sans JP", sans-serif;
    --font-mono: "IBM Plex Mono", ui-monospace, "SF Mono", Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #14161a; --surface: #1b1e24; --surface-2: #22262e; --ink: #eeece4;
      --ink-muted: #9a9a8f; --ink-faint: #6c6a60; --hairline: #2c2f37;
      --accent: #dcae51; --accent-ink: #1a1305; --bull: #5cb787; --bull-soft: #1c3327;
      --bear: #de7259; --bear-soft: #3a241e; --neutral: #8f9299; --neutral-soft: #2a2d33;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.4), 0 12px 28px -16px rgba(0, 0, 0, 0.6);
    }
  }
  :root[data-theme="dark"] {
    --bg: #14161a; --surface: #1b1e24; --surface-2: #22262e; --ink: #eeece4;
    --ink-muted: #9a9a8f; --ink-faint: #6c6a60; --hairline: #2c2f37;
    --accent: #dcae51; --accent-ink: #1a1305; --bull: #5cb787; --bull-soft: #1c3327;
    --bear: #de7259; --bear-soft: #3a241e; --neutral: #8f9299; --neutral-soft: #2a2d33;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.4), 0 12px 28px -16px rgba(0, 0, 0, 0.6);
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--ink); font-family: var(--font-body); line-height: 1.6; -webkit-font-smoothing: antialiased; }
  @media (prefers-reduced-motion: no-preference) {
    body { animation: fadeIn 420ms ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
    @keyframes revealIn { from { opacity: 0; transform: translateY(-3px); } to { opacity: 1; transform: none; } }
  }
  .page { max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }
  header.masthead {
    display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between;
    gap: 16px; padding-bottom: 20px; margin-bottom: 28px; border-bottom: 2px solid var(--ink);
  }
  .masthead h1 { font-family: var(--font-display); font-weight: 700; font-size: clamp(1.7rem, 3vw, 2.3rem); margin: 0 0 4px; text-wrap: balance; letter-spacing: 0.02em; }
  .masthead .sub { color: var(--ink-muted); font-size: 0.88rem; }
  .chip { font-family: var(--font-mono); font-size: 0.75rem; padding: 5px 10px; border-radius: 999px; border: 1px solid var(--hairline); color: var(--ink-muted); background: var(--surface); }
  .back-link { display: inline-block; margin: 0 18px 24px 0; font-size: 0.82rem; font-family: var(--font-mono); color: var(--accent); text-decoration: none; }
  .back-link:hover { text-decoration: underline; }

  .sector-block { margin-bottom: 30px; }
  .sector-title { font-family: var(--font-display); font-weight: 700; font-size: 1.4rem; margin: 0 0 14px; }
  .boards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 860px) { .boards { grid-template-columns: 1fr; } }
  .board { background: var(--surface); border: 1px solid var(--hairline); border-radius: 12px; box-shadow: var(--shadow); overflow: hidden; container-type: inline-size; container-name: board; }
  .board-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid var(--hairline); background: var(--surface-2); }
  .board-head h3 { font-family: var(--font-display); font-weight: 500; font-size: 1.05rem; margin: 0; }
  .board-count { font-family: var(--font-mono); font-size: 0.75rem; color: var(--ink-muted); }

  .row { border-bottom: 1px solid var(--hairline); }
  .row:last-child { border-bottom: none; }
  .row summary { list-style: none; cursor: pointer; display: grid; grid-template-columns: 1fr auto 132px auto; align-items: center; gap: 12px; padding: 12px 18px; transition: background 120ms ease-out; }
  .row summary::-webkit-details-marker { display: none; }
  .row summary:hover { background: var(--surface-2); }
  @media (prefers-reduced-motion: no-preference) {
    .row[open] > .detail { animation: revealIn 220ms ease-out; }
  }
  .chart-link { font-family: var(--font-mono); font-size: 0.72rem; color: var(--accent); text-decoration: none; white-space: nowrap; border: 1px solid var(--accent); border-radius: 999px; padding: 4px 10px; transition: background 120ms ease-out, color 120ms ease-out; }
  .chart-link:hover { background: var(--accent); color: var(--accent-ink); }
  .name-block { min-width: 0; display: flex; flex-direction: column; gap: 1px; }
  .ticker { font-family: var(--font-mono); font-weight: 600; font-size: 0.92rem; }
  .company { display: block; min-width: 0; color: var(--ink-muted); font-size: 0.78rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .price { font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: 0.88rem; text-align: right; }

  .gauges { display: flex; gap: 6px; }
  .gauge { display: flex; flex-direction: column; align-items: center; gap: 3px; width: 38px; }
  .gauge-label { font-size: 0.62rem; color: var(--ink-faint); font-family: var(--font-mono); }
  .gauge-track { position: relative; width: 100%; height: 6px; background: var(--neutral-soft); border-radius: 3px; overflow: hidden; }
  .gauge-fill { position: absolute; top: 0; bottom: 0; width: 0; background: var(--bull); }
  .gauge-fill.neg { background: var(--bear); }
  @media (prefers-reduced-motion: no-preference) {
    .gauge-fill { transition: width 650ms cubic-bezier(0.22, 1, 0.36, 1) 60ms, left 650ms cubic-bezier(0.22, 1, 0.36, 1) 60ms; }
  }

  .detail { padding: 4px 18px 18px 18px; display: grid; gap: 14px; }
  .detail-section h3 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-faint); margin: 0 0 8px; }
  .score-table { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .score-card { border: 1px solid var(--hairline); border-radius: 8px; padding: 8px 10px; background: var(--surface-2); }
  .score-card .term { font-size: 0.7rem; color: var(--ink-faint); }
  .score-card .label { font-weight: 600; font-size: 0.85rem; margin-top: 2px; }
  .score-card .val { font-family: var(--font-mono); font-size: 0.72rem; color: var(--ink-muted); }
  .label.bull-strong, .label.bull { color: var(--bull); }
  .label.bear-strong, .label.bear { color: var(--bear); }
  .label.neutral { color: var(--neutral); }

  .insight-line { font-family: var(--font-display); font-size: 0.92rem; line-height: 1.7; margin: 0 0 10px; padding: 8px 12px; background: var(--surface-2); border-left: 3px solid var(--accent); border-radius: 0 6px 6px 0; }
  .tech-extra { display: flex; flex-direction: column; gap: 6px; font-size: 0.85rem; }
  .tech-extra-row { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px dashed var(--hairline); padding-bottom: 4px; }
  .tech-extra-row .term { color: var(--ink-muted); }

  .headline-list { display: grid; gap: 2px; }
  .headline { display: grid; grid-template-columns: 92px 1fr; align-items: baseline; gap: 10px; font-size: 0.8rem; padding: 5px 6px; border-radius: 6px; color: var(--ink); text-decoration: none; }
  a.headline:hover { background: var(--surface-2); }
  div.headline { color: var(--ink); }
  .headline time { font-family: var(--font-mono); color: var(--ink-faint); font-size: 0.72rem; }

  .empty-state { padding: 40px 18px; text-align: center; color: var(--ink-faint); font-size: 0.85rem; }
  footer.note { margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--hairline); color: var(--ink-faint); font-size: 0.76rem; line-height: 1.7; }

  @container board (max-width: 520px) {
    .row summary { grid-template-columns: 1fr auto 92px auto; gap: 7px; padding: 10px 12px; }
    .chart-link { padding: 4px 7px; font-size: 0; }
    .chart-link::after { content: "↗"; font-size: 0.85rem; }
    .gauge { width: 26px; }
    .gauge-label { display: none; }
  }
</style>

<div class="page">
  <header class="masthead">
    <div>
      <h1>セクター・ウォッチリストボード</h1>
      <div class="sub">宇宙・防衛・船舶・メモリ半導体 — 日米定点観測</div>
    </div>
    <span class="chip" id="updatedChip"></span>
  </header>

  <a class="back-link" href="https://claude.ai/code/artifact/aae8bc26-18de-4aaf-964b-9ef16ccbd3f7" target="_blank" rel="noopener">📈 相場ボードを見る ↗</a>

  <div id="sectors"></div>

  <footer class="note">
    短期・中期・長期のスコアは移動平均線を主とした複数のテクニカル指標(SMA/EMA・MACD・RSI・ストキャスティクス・ボリンジャーバンド・ADX・一目均衡表・出来高・ダウ理論・ワイコフ法・ローソク足パターン・フィボナッチ・ボリュームプロファイル)を加重平均した参考値です（+1に近いほど強気、-1に近いほど弱気）。この銘柄リストは固定のウォッチリストであり、動的なスクリーニングは行っていません。いずれも自動生成された参考情報であり、投資助言ではありません。投資判断はご自身の責任で行ってください。
  </footer>
</div>

<script>
  const LABEL_CLASS = {
    "強気（上昇優勢）": "bull-strong", "やや強気": "bull", "中立": "neutral",
    "やや弱気": "bear", "弱気（下落優勢）": "bear-strong",
  };
  const WYCKOFF_LABEL = { accumulation: "蓄積", markup: "上昇", distribution: "分配", markdown: "下降", undefined: "判定不能" };
  const TREND_PHRASE = { up: "上昇トレンド", down: "下降トレンド", sideways: "方向感の乏しいレンジ" };
  const WYCKOFF_PHRASE = {
    markup: "ワイコフ的には上昇（マークアップ）局面", accumulation: "ワイコフ的には蓄積局面",
    distribution: "ワイコフ的には分配局面", markdown: "ワイコフ的には下降（マークダウン）局面",
  };
  const PATTERN_PHRASE = {
    bullish_engulfing: "直近では強気の包み足が出現", bearish_engulfing: "直近では弱気の包み足が出現",
    hammer: "直近でハンマー（下ヒゲ）が出現", shooting_star: "直近で上ヒゲの長い足が出現",
    doji: "直近で迷いを示す十字線が出現",
  };

  function fmtNum(n, digits = 2) {
    if (n === null || n === undefined || Number.isNaN(n)) return "—";
    return Number(n).toLocaleString("ja-JP", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }
  function fmtDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso).slice(0, 10);
    return d.toLocaleString("ja-JP", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  }
  function escapeAttr(s) {
    return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
  }
  function companyName(item) { return item.name_ja || item.name || ""; }
  function chartUrl(ticker) {
    const code = ticker.endsWith(".T") ? `${ticker.slice(0, -2)}-JP` : `${ticker}-US`;
    return `https://www.moomoo.com/ja/stock/${encodeURIComponent(code)}`;
  }

  function gauge(term, score) {
    const pct = Math.min(Math.abs(score), 1) * 50;
    const isNeg = score < 0;
    const left = isNeg ? 50 - pct : 50;
    return `<div class="gauge">
      <span class="gauge-label">${term}</span>
      <div class="gauge-track">
        <div class="gauge-fill ${isNeg ? "neg" : ""}" data-left="${left}" data-width="${pct}" style="left:${left}%;"></div>
      </div>
    </div>`;
  }
  function animateGauges() {
    requestAnimationFrame(() => {
      document.querySelectorAll(".gauge-fill[data-width]").forEach((el) => { el.style.width = `${el.dataset.width}%`; });
    });
  }
  function scoreCard(term, obj) {
    const cls = LABEL_CLASS[obj.label] || "neutral";
    return `<div class="score-card">
      <div class="term">${term}</div>
      <div class="label ${cls}">${obj.label}</div>
      <div class="val">スコア ${obj.score >= 0 ? "+" : ""}${fmtNum(obj.score, 3)}</div>
    </div>`;
  }
  function insightLine(t) {
    const dow = t.dow_theory || {};
    const dowDaily = dow.daily || {};
    const wyckoff = t.wyckoff_phase || {};
    const candle = t.candlestick_pattern || {};
    const trend = TREND_PHRASE[dowDaily.trend];
    if (!trend) return "";
    const volNote = dowDaily.confirmed_by_volume ? "（出来高の裏付けあり）" : "";
    const phase = WYCKOFF_PHRASE[wyckoff.phase];
    const pattern = PATTERN_PHRASE[candle.pattern];
    let text = `日足は${trend}${volNote}`;
    if (phase) text += `、${phase}`;
    text += "。";
    if (pattern) text += `${pattern}。`;
    return `<p class="insight-line">${text}</p>`;
  }
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
      ${insightLine(t)}
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

  function row(item) {
    const t = item.technical;
    const headlines = (item.fundamentals_raw || []).slice(0, 5).map((h) => {
      const text = h.title_ja || h.title || "";
      const hasOriginal = h.title_ja && h.title && h.title_ja !== h.title;
      const tip = hasOriginal ? ` title="${escapeAttr(h.title)}"` : "";
      const url = h.link || h.document_url || "";
      const inner = `<time>${fmtDate(h.published_at)}</time><span${tip}>${text}</span>`;
      return url
        ? `<a class="headline" href="${escapeAttr(url)}" target="_blank" rel="noopener">${inner}</a>`
        : `<div class="headline">${inner}</div>`;
    }).join("") || `<div class="headline"><span>直近の材料は見つかりませんでした</span></div>`;

    return `<details class="row">
      <summary>
        <span class="name-block">
          <span class="ticker">${item.ticker}</span>
          <span class="company">${companyName(item)}</span>
        </span>
        <span class="price">${fmtNum(item.price)}</span>
        <span class="gauges">
          ${gauge("短", t.short_term.score)}
          ${gauge("中", t.mid_term.score)}
          ${gauge("長", t.long_term.score)}
        </span>
        <a class="chart-link" href="${chartUrl(item.ticker)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">チャート ↗</a>
      </summary>
      <div class="detail">
        <div class="detail-section">
          <h3>テクニカル内訳</h3>
          <div class="score-table">
            ${scoreCard("短期", t.short_term)}
            ${scoreCard("中期", t.mid_term)}
            ${scoreCard("長期", t.long_term)}
          </div>
        </div>
        <div class="detail-section">
          <h3>ファンダメンタルズ材料（${item.fundamentals_source || "—"}）</h3>
          <div class="headline-list">${headlines}</div>
        </div>
        ${technicalDetailSection(t)}
      </div>
    </details>`;
  }

  function renderBoard(items) {
    if (!items || !items.length) return `<div class="empty-state">対象銘柄がありません</div>`;
    return items.map(row).join("");
  }

  function renderSectors(sectors) {
    const el = document.getElementById("sectors");
    el.innerHTML = sectors.map((sector) => `
      <section class="sector-block">
        <h2 class="sector-title">${sector.name}</h2>
        <div class="boards">
          <section class="board">
            <div class="board-head"><h3>米国株</h3><span class="board-count">${(sector.us || []).length}銘柄</span></div>
            <div>${renderBoard(sector.us)}</div>
          </section>
          <section class="board">
            <div class="board-head"><h3>日本株</h3><span class="board-count">${(sector.jp || []).length}銘柄</span></div>
            <div>${renderBoard(sector.jp)}</div>
          </section>
        </div>
      </section>
    `).join("");
  }

  fetch("sector_watchlist_data.json")
    .then((r) => r.json())
    .then((data) => {
      document.getElementById("updatedChip").textContent = `更新: ${fmtDate(data.generated_at)}`;
      renderSectors(data.sectors || []);
      animateGauges();
    })
    .catch((err) => {
      document.getElementById("sectors").innerHTML = `<div class="empty-state">データの読み込みに失敗しました: ${err}</div>`;
    });
</script>
```

- [ ] **Step 3: サンプルデータでローカル確認**

`stock-data-tool/dashboard/sector_watchlist_data.json`に以下のサンプルを一時的に配置する（動作確認後は削除、コミットしない）:

```json
{
  "generated_at": "2026-09-21T09:00:00+09:00",
  "sectors": [
    {
      "name": "宇宙",
      "us": [
        {
          "ticker": "SPCX", "name": "SpaceX", "name_ja": null, "price": 152.71, "price_source": "yfinance",
          "technical": {
            "short_term": {"score": 0.17, "label": "中立"},
            "mid_term": {"score": 0.47, "label": "やや強気"},
            "long_term": {"score": 0.06, "label": "中立"},
            "dow_theory": {"daily": {"trend": "up", "confirmed_by_volume": true}, "weekly": {"trend": "up", "confirmed_by_volume": false}},
            "wyckoff_phase": {"phase": "distribution"},
            "candlestick_pattern": {"pattern": null},
            "fibonacci_position": {"price_zone": "0.500"},
            "volume_profile": {"price_vs_poc": 0.02}
          },
          "fundamentals_source": "Yahoo Finance News",
          "fundamentals_raw": [{"title": "Sample headline", "title_ja": "サンプル見出し", "published_at": "2026-09-20T10:00:00+09:00", "link": "https://example.com"}]
        }
      ],
      "jp": [
        {
          "ticker": "9348.T", "name": "ispace", "name_ja": "ispace", "price": 416.0, "price_source": "yfinance",
          "technical": {
            "short_term": {"score": 0.09, "label": "中立"},
            "mid_term": {"score": -0.32, "label": "やや弱気"},
            "long_term": {"score": -0.71, "label": "弱気（下落優勢）"},
            "dow_theory": {"daily": {"trend": "down", "confirmed_by_volume": false}, "weekly": {}},
            "wyckoff_phase": {"phase": "accumulation"},
            "candlestick_pattern": {"pattern": "shooting_star"},
            "fibonacci_position": {},
            "volume_profile": {}
          },
          "fundamentals_source": "TDnet",
          "fundamentals_raw": []
        }
      ]
    }
  ]
}
```

`.claude/launch.json`の`dashboard`設定（`python -m http.server 8877 --directory dashboard`）でローカルサーバーを起動し、`http://localhost:8877/sector-watchlist.html`を開く。以下を確認する:
- ヘッダーの更新日時が正しく表示される
- 「宇宙」セクションの米国株ボードにSpaceXの行が表示され、ゲージがアニメーションで塗り込まれる
- 行を展開すると、見立て文・テクニカル内訳・ファンダメンタルズ材料が表示される
- 「チャート ↗」リンクが`https://www.moomoo.com/ja/stock/SPCX-US`を指している
- 「宇宙」セクションの日本株ボードにispaceの行が表示され、展開すると「直近の材料は見つかりませんでした」（空の`fundamentals_raw`）と、週足トレンド等の欠落フィールドが「—」表示になり、例外が発生しないことを確認する
- ブラウザのコンソールにエラーが出ていない
- 確認後、`dashboard/sector_watchlist_data.json`を削除する（コミット対象に含めない）

- [ ] **Step 4: コミット**

```bash
git add dashboard/sector-watchlist.html
git commit -m "feat: add sector watchlist dashboard page"
```

---

## Task 4: 実データでの通し確認とスケジュールタスク作成

**Files:** なし（コードタスクではなく、実行・確認・スケジュール設定のタスク）

**Interfaces:**
- Consumes: Task 1〜3で作成した`generate_sector_watchlist.py`と`dashboard/sector-watchlist.html`

- [ ] **Step 1: 実データでスクリプトを1回実行**

`stock-data-tool/`ディレクトリで実行:

```bash
python generate_sector_watchlist.py
```

Expected: `wrote dashboard/sector_watchlist_data.json (30/30 tickers)`のような出力。一部銘柄の取得に失敗した場合は`failed to build report for {ticker}: {exc}`が表示されるが、処理は継続して完了する。

- [ ] **Step 2: 生成されたJSONの中身を確認**

`dashboard/sector_watchlist_data.json`を開き、4セクション分の`sectors`配列があり、各`us`/`jp`配列に該当銘柄のエントリーが入っていることを確認する。特に`7011.T`（三菱重工業）が「宇宙」「防衛」両方のセクションに現れることを確認する。

- [ ] **Step 3: ブラウザで最終確認**

ローカルサーバーで`http://localhost:8877/sector-watchlist.html`を開き、実データで全4セクション×日米が正しく表示されること、コンソールエラーがないことを確認する。

- [ ] **Step 4: 実行タイミングをユーザーに確認**

ユーザーに希望の実行時刻を確認する（例: 「毎朝7時」等）。spec記載の通り、具体的な時刻はここで確定する。

- [ ] **Step 5: Claude Codeのスケジュールタスクを作成**

`mcp__scheduled-tasks__create_scheduled_task`（または対応するツール）で、Step 4で確認した時刻に`python generate_sector_watchlist.py`を`stock-data-tool/`ディレクトリで実行するスケジュールタスクを作成する。プロンプトには最低限「`stock-data-tool`ディレクトリで`python generate_sector_watchlist.py`を実行し、成功したか（何銘柄取得できたか）を報告する」ことを含める。

- [ ] **Step 6: 初回スケジュール実行を確認**

作成したスケジュールタスクを試験的に一度手動実行し（対応するツールがあれば）、正常終了すること、`dashboard/sector_watchlist_data.json`が更新されることを確認する。
