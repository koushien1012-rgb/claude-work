import json

from analysis import analyze_news
from news import get_tdnet_disclosures, get_yfinance_news

if __name__ == "__main__":
    ticker = "AAPL"
    news_items = get_yfinance_news(ticker, limit=8)
    result = analyze_news(ticker, news_items)
    print(f"=== {ticker} ファンダメンタルズ分析 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print()
    jp_ticker = "7203"
    disclosures = get_tdnet_disclosures(code=jp_ticker, limit=8)
    result_jp = analyze_news(jp_ticker, disclosures)
    print(f"=== トヨタ({jp_ticker}) ファンダメンタルズ分析 ===")
    print(json.dumps(result_jp, ensure_ascii=False, indent=2))
