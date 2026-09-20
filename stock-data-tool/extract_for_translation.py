import json

with open("output/watchlist/dashboard_data.json", encoding="utf-8") as f:
    data = json.load(f)

out = {"macro_news": [], "markets": {}}

for item in data.get("macro_news", []):
    out["macro_news"].append({"title": item.get("title")})

for mkey, mval in data.get("markets", {}).items():
    out["markets"][mkey] = {}
    for cat, stocks in mval.items():
        out["markets"][mkey][cat] = []
        for s in stocks:
            headlines = []
            for h in (s.get("fundamentals_raw") or []):
                headlines.append({"title": h.get("title"), "published_at": h.get("published_at")})
            out["markets"][mkey][cat].append({
                "ticker": s.get("ticker"),
                "name": s.get("name"),
                "sector": s.get("sector"),
                "fundamentals_source": s.get("fundamentals_source"),
                "technical": s.get("technical"),
                "combined": s.get("combined"),
                "headlines": headlines,
            })

with open("scratch_condensed.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("wrote scratch_condensed.json")
