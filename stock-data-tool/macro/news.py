from news import get_yfinance_news

_PROXIES = {"市況全般": "SPY", "金": "GC=F", "原油(WTI)": "CL=F"}


def get_macro_news(limit_per_proxy: int = 4) -> list[dict]:
    items = []
    for label, ticker in _PROXIES.items():
        try:
            for item in get_yfinance_news(ticker, limit=limit_per_proxy):
                items.append({**item, "proxy": label})
        except Exception:
            continue
    return items
