import json

from news import get_tdnet_disclosures, get_yfinance_news

if __name__ == "__main__":
    print("=== AAPL news (Yahoo Finance) ===")
    aapl_news = get_yfinance_news("AAPL", limit=5)
    print(json.dumps(aapl_news, ensure_ascii=False, indent=2))

    print()
    print("=== トヨタ(7203) TDnet 適時開示 ===")
    toyota_disclosures = get_tdnet_disclosures(code="7203", limit=5)
    print(json.dumps(toyota_disclosures, ensure_ascii=False, indent=2))
