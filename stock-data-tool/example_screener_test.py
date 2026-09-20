from screener import get_nikkei225_tickers, get_sp500_tickers, scan_universe, top_signals

if __name__ == "__main__":
    nikkei = get_nikkei225_tickers()
    sp500 = get_sp500_tickers()
    print(f"nikkei225: {len(nikkei)} tickers, sample: {nikkei[:5]}")
    print(f"sp500: {len(sp500)} tickers, sample: {sp500[:5]}")

    print()
    print("=== quick scan test (first 20 nikkei tickers) ===")
    scan_df = scan_universe(nikkei[:20], period="1y")
    print(scan_df)
