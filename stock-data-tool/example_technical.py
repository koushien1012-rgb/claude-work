import json

from analysis import compute_indicators, outlook
from stock_data import get_daily

TICKERS = ["AAPL", "7203.T"]

if __name__ == "__main__":
    for ticker in TICKERS:
        df = get_daily(ticker, source="yfinance", period="2y")
        indicators = compute_indicators(df)
        result = outlook(indicators, df)
        print(f"=== {ticker} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
