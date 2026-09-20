# 相場ボード：テクニカル分析スキルベースの銘柄選定 設計書

- 日付: 2026-09-20
- 対象: `stock-data-tool` の「相場ボード」（`dashboard/index.html`）
- 対象外: 「セクター相場ボード」（`dashboard/sector-board.html`）は、Claudeがコメント生成時に技術的視点として参照するのみで、選定ロジックは変更しない

## 背景・目的

現在の相場ボードは `screener/scan.py` → `analysis/signals.py` の `outlook()` が、移動平均クロス・MACD・RSI・ストキャスティクス・ボリンジャーバンド・ADX・一目均衡表・出来高（OBV）を重み付けしたスコアで上位10銘柄（強気/弱気 × 日本株/米国株）を選定している。

インストールした `technical-analysis` スキル（ダウ理論・ワイコフ法・ローソク足・フィボナッチ・エリオット波動・ボリュームプロファイル・マルチタイムフレーム分析を含む）の知見を、この選定ロジックに統合する。

## スコープ

- 含む: ダウ理論、ワイコフ法、ローソク足パターン、フィボナッチ、ボリュームプロファイル、マルチタイムフレーム（週足/日足/4時間足）、最終上位10銘柄のチャート可視化
- 含む（参考情報のみ・スコア非算入）: エリオット波動
- 含まない: 自動売買、リアルタイム更新、セクター相場ボードの選定ロジック変更

## アーキテクチャ：2段階パイプライン

### 第1段階：全700銘柄スキャン（既存の日足データのみ）

- 既存の `scan_universe()`（`screener/scan.py`）の入出力形状は変えない（yfinance, period="1y", 日経225+S&P500 ≒ 700銘柄）
- `analysis/technical.py` の `compute_indicators()` に、新規指標の計算を追加
- `analysis/signals.py` の `outlook()` に、新規スコア要素を統合
- 出力：候補プール30〜50銘柄（強気/弱気それぞれ、日本株/米国株それぞれ）に絞り込み（現行の10銘柄より広め）

### 第2段階：候補銘柄のみ精査（新規）

- 第1段階の候補プールのみ、`stock_data.get_intraday(ticker, interval="60m", period="60d")` で1時間足を取得し、4時間足へリサンプル
- 週足→日足→4時間足の整合性を確認し、エントリー精度を精査
- ここで最終的な上位10銘柄（強気/弱気 × JP/US）を確定
- エリオット波動の推定波動ラベルを、スコアに使わず参考情報として付加
- 最終10銘柄についてのみ、チャート可視化用のOHLCVデータとアノテーションを生成

## 新規モジュール（`analysis/`配下）

| モジュール | 責務 | 入力 | 出力 |
|---|---|---|---|
| `dow_theory.py` | フラクタル法でスイング高値・安値を検出し、HH/HL（上昇継続）・LH/LL（下降継続）のトレンド構造を判定。日足・週足それぞれに適用可能 | OHLCV DataFrame | `{trend: "up"\|"down"\|"sideways", last_swings: [...], confirmed_by_volume: bool}` |
| `wyckoff.py` | レンジ幅の収縮/拡大と出来高パターンから蓄積・上昇・分配・下降の簡易フェーズを推定 | OHLCV DataFrame | `{phase: "accumulation"\|"markup"\|"distribution"\|"markdown"\|"undefined", since: date}` |
| `candlestick.py` | 直近1〜3本から主要な日本足パターン（包み足・ハンマー/首吊り線・大陰陽線・星形）を検出 | OHLCV DataFrame | `{pattern: str\|None, direction: 1\|-1\|0, bar_index: int}` |
| `fibonacci.py` | `dow_theory` が検出した直近の有意なスイングからリトレースメント/エクステンション水準を算出し、現在値の位置を評価 | OHLCV DataFrame, スイング情報 | `{levels: {...}, price_zone: str, score: float}` |
| `volume_profile.py` | 終値×出来高のヒストグラムから簡易POC（出来高最多価格帯）と価値エリアを推定 | OHLCV DataFrame | `{poc: float, value_area: (float, float), price_vs_poc: float}` |

いずれも既存の `analysis/technical.py` の指標関数群と同じ関数ベースのスタイル（純粋関数、pandas DataFrame入出力）に合わせる。

## スコア統合（`analysis/signals.py`）

ダウ理論の trend hierarchy（primary/secondary/minor）を、既存の3層スコア（long/mid/short term）にそのまま対応させる。

- **short_term（minor＝短期の値動き）**: 既存（RSI/ストキャス/MACDモメンタム/ボリンジャー/出来高確認）＋ `candlestick.py` パターンシグナル ＋ `fibonacci.py` 現在値の位置評価
- **mid_term（secondary＝日足トレンド）**: 既存（SMA25vs75/価格vsSMA25/MACDトレンド/ADX/出来高確認）＋ `dow_theory.py` 日足トレンド構造 ＋ `wyckoff.py` フェーズ
- **long_term（primary＝週足トレンド）**: 既存（SMA75vs200/価格vsSMA200/一目均衡表/ADX）＋ `dow_theory.py` 週足トレンド構造 ＋ `volume_profile.py` POCとの位置関係

新規スコア要素は、既存の `_score_*` 関数と同じ `-1.0〜1.0` のレンジに正規化し、`SHORT_TERM_WEIGHTS` / `MID_TERM_WEIGHTS` / `LONG_TERM_WEIGHTS` に追加する。重みの初期値は既存項目と同程度（1.0〜2.0）から始め、第1段階の検証時に調整する。

`top_signals()`（現行の avg_score 加重平均によるランキング）のロジックは変更しない。

## データ・スキーマ変更

### `generate_daily_watchlist.py` / `analysis/report.py`

`_ticker_entry()` の `technical` フィールド配下に以下を追加：

```
technical.dow_theory: { daily: {...}, weekly: {...} }
technical.wyckoff_phase: {...}
technical.candlestick_pattern: {...}
technical.fibonacci_position: {...}
technical.volume_profile: {...}
```

最終上位10銘柄（第2段階を通過した銘柄）のみ、以下を追加：

```
entry_timeframe: {
  alignment: "aligned" | "conflicting",   // 週足/日足/4時間足の整合性
  elliott_wave_context: string,            // 参考情報のみ、スコア非算入
  note: string
}
chart: {
  ohlcv: [{date, open, high, low, close, volume}, ...],  // 直近120〜180日分
  annotations: {
    swings: [{date, price, type: "high"|"low"}, ...],
    fibonacci_levels: [{level: 0.382, price: float}, ...],
    wyckoff_zones: [{start: date, end: date, phase: string}, ...],
    candlestick_markers: [{date, pattern: string, direction: 1|-1}, ...]
  }
}
```

`chart` フィールドは最終上位10銘柄（各市場・強気/弱気で最大40銘柄相当）にのみ含め、全700銘柄分は含めない（JSONサイズを抑えるため）。

### `dashboard/index.html`

- 既存のサマリー行（順位・銘柄名・価格・短中長期ゲージ）は変更しない
- 展開表示（`<details>`）内に、新規指標の内訳表示を追加（既存の `scoreCard()` と同様のスタイル）
- `chart` フィールドが存在する銘柄（＝最終上位10銘柄）には、TradingView製「Lightweight Charts」（CDN経由、MITライセンス）でローソク足チャートを描画し、`annotations` の内容をオーバーレイ表示：
  - スイング高値・安値：マーカー
  - フィボナッチ水準：水平線
  - ワイコフフェーズ：背景帯の色分け
  - ローソク足パターン検出箇所：矢印マーカー
  - 出来高：下段バーチャート
- 既存の「チャート ↗」リンク（Yahoo!ファイナンス外部リンク）はそのまま残す（補完的な位置づけ）

## 検証方法

このプロジェクトに自動テストはないため、以下の手順で手動検証する：

1. 各新規モジュールを、既存の `output/watchlist/top_bullish.csv` 等にある実在銘柄数件（例：直近の上位銘柄）に適用し、スイング検出・フェーズ判定・パターン検出が実チャート（Yahoo!ファイナンス等）と整合するか目視確認
2. 第1段階のスコア統合後、`scan_universe()` の実行時間が現行から大きく増えていないか確認（700銘柄規模でのパフォーマンス確認）
3. 第2段階の4時間足取得が候補プール30〜50銘柄規模で現実的な時間内に完了するか確認
4. `dashboard_data.json` の出力サイズが極端に大きくなっていないか確認（chart データは上位10銘柄のみに限定しているため）
5. ダッシュボードをブラウザで開き、チャート描画とオーバーレイが正しく表示されるか確認

## 既知の制約・リスク

- yfinanceの60分足データは直近60日分までしか取得できない（yfinanceの制限）。4時間足へのリサンプルはこの範囲内で行う
- ワイコフフェーズ判定・ローソク足パターン認識は、価格・出来高のみからのヒューリスティックであり、完全な精度は保証しない。あくまで参考情報としての位置づけとし、既存指標と合わせた総合判断とする
- エリオット波動はスコアに使わない（スキル自身の "予測ツールとしては危険" という指摘に従う）
