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
         patch("analysis.report.get_next_earnings_date", return_value=None), \
         patch("analysis.report.get_business_summary_en", return_value=None):
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


def test_generate_report_translates_us_news_titles_to_japanese():
    df = _fake_df()
    news = [{"title": "Nvidia reports strong earnings", "summary": "", "published_at": "2026-09-20"}]
    with patch("analysis.report.get_daily", return_value=df), \
         patch("analysis.report.get_macro_daily", return_value=df), \
         patch("analysis.report.get_yfinance_news", return_value=news), \
         patch("analysis.report.get_next_earnings_date", return_value=None), \
         patch("analysis.report.get_business_summary_en", return_value=None), \
         patch("analysis.report.translate_to_ja", return_value="エヌビディアが好調な決算を発表"):
        report = generate_report("NVDA", name="NVIDIA")

    assert report["fundamentals_source"] == "Yahoo Finance News"
    assert report["fundamentals_raw"][0]["title_ja"] == "エヌビディアが好調な決算を発表"


def test_generate_report_does_not_translate_jp_tdnet_titles():
    df = _fake_df()
    disclosures = [{"title": "決算発表のお知らせ", "company_name": "テスト", "published_at": "2026-09-20"}]
    with patch("analysis.report.get_daily", return_value=df), \
         patch("analysis.report.get_macro_daily", return_value=df), \
         patch("analysis.report.get_tdnet_disclosures", return_value=disclosures), \
         patch("analysis.report.get_next_earnings_date", return_value=None), \
         patch("analysis.report.get_business_summary_en", return_value=None), \
         patch("analysis.report.translate_to_ja") as mock_translate:
        report = generate_report("7011.T", name="三菱重工業")

    assert report["fundamentals_source"] == "TDnet"
    assert "title_ja" not in report["fundamentals_raw"][0]
    mock_translate.assert_not_called()


def test_generate_report_includes_translated_business_summary():
    df = _fake_df()
    with patch("analysis.report.get_daily", return_value=df), \
         patch("analysis.report.get_macro_daily", return_value=df), \
         patch("analysis.report.get_tdnet_disclosures", return_value=[]), \
         patch("analysis.report.get_yfinance_news", return_value=[]), \
         patch("analysis.report.get_next_earnings_date", return_value=None), \
         patch("analysis.report.get_business_summary_en", return_value="Acme Corp makes widgets."), \
         patch("analysis.report.business_summary_ja", return_value="アクメ社はウィジェットを製造しています。"):
        report = generate_report("ACME", name="Acme Corp")

    assert report["business_summary_ja"] == "アクメ社はウィジェットを製造しています。"
