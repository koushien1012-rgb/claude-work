from stock_data import get_daily, get_intraday, save_csv

if __name__ == "__main__":
    daily = get_daily("AAPL", source="yfinance", period="1mo")
    print(daily.tail())
    save_csv(daily, "output/AAPL_daily.csv")

    intraday = get_intraday("AAPL", source="yfinance", interval="5m", period="5d")
    print(intraday.tail())
    save_csv(intraday, "output/AAPL_5m.csv")

    # Alpha Vantage / FMP require an API key in .env
    # daily_av = get_daily("AAPL", source="alphavantage")
    # daily_fmp = get_daily("AAPL", source="fmp")
