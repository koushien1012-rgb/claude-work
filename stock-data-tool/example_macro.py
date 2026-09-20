from analysis import compute_indicators, outlook
from macro import get_macro_daily, get_macro_snapshot

if __name__ == "__main__":
    print("=== マクロ市場スナップショット ===")
    snapshot = get_macro_snapshot()
    print(snapshot.to_string(index=False))

    print()
    print("=== 日経平均(^N225) テクニカル見通し ===")
    df = get_macro_daily("nikkei225", period="2y")
    result = outlook(compute_indicators(df), df)
    print(f"短期: {result['short_term']['label']} ({result['short_term']['score']})")
    print(f"中期: {result['mid_term']['label']} ({result['mid_term']['score']})")
    print(f"長期: {result['long_term']['label']} ({result['long_term']['score']})")
