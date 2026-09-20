import requests

from stock_data.common import get_env

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

_cik_cache: dict | None = None


def _headers() -> dict:
    contact = get_env("SEC_EDGAR_CONTACT")
    if not contact:
        raise RuntimeError(
            "SEC_EDGAR_CONTACT is not set. Add a line like "
            "'SEC_EDGAR_CONTACT=YourName your@email.com' to .env "
            "(SEC EDGAR requires a contact string in the User-Agent header)."
        )
    return {"User-Agent": contact}


def _load_cik_map() -> dict:
    global _cik_cache
    if _cik_cache is None:
        resp = requests.get(_TICKERS_URL, headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _cik_cache = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in data.values()}
    return _cik_cache


def get_recent_filings(ticker: str, forms: tuple = ("8-K",), limit: int = 20) -> list[dict]:
    cik = _load_cik_map().get(ticker.upper())
    if not cik:
        raise ValueError(f"CIK not found for ticker '{ticker}'.")
    resp = requests.get(_SUBMISSIONS_URL.format(cik=cik), headers=_headers(), timeout=30)
    resp.raise_for_status()
    recent = resp.json().get("filings", {}).get("recent", {})
    results = []
    for i, form in enumerate(recent.get("form", [])):
        if form not in forms:
            continue
        accession = recent["accessionNumber"][i].replace("-", "")
        document = recent["primaryDocument"][i]
        results.append({
            "form": form,
            "filed_at": recent["filingDate"][i],
            "report_date": recent["reportDate"][i],
            "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{document}",
        })
        if len(results) >= limit:
            break
    return results
