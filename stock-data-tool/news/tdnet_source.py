import requests

# Unofficial community mirror of TDnet (Tokyo Stock Exchange timely disclosures).
# No API key required. https://webapi.yanoshin.jp/
_BASE_URL = "https://webapi.yanoshin.jp/webapi/tdnet/list"


def get_disclosures(code: str | None = None, date: str | None = None, limit: int = 20) -> list[dict]:
    target = code if code else (date or "recent")
    resp = requests.get(f"{_BASE_URL}/{target}.json", params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for entry in data.get("items", []):
        tdnet = entry.get("Tdnet", {})
        results.append({
            "company_code": tdnet.get("company_code"),
            "company_name": tdnet.get("company_name"),
            "title": tdnet.get("title"),
            "published_at": tdnet.get("pubdate"),
            "document_url": tdnet.get("document_url"),
        })
    return results
