import json
from pathlib import Path

from deep_translator import MyMemoryTranslator

from stock_data.common import get_env

_TITLE_CACHE_PATH = Path("output/cache/translation_cache.json")
_BUSINESS_SUMMARY_CACHE_PATH = Path("output/cache/business_summary_ja.json")
_BUSINESS_SUMMARY_EXCERPT_CHARS = 400


def _load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def translate_to_ja(text: str | None) -> str | None:
    text = (text or "").strip()
    if not text:
        return None

    cache = _load_cache(_TITLE_CACHE_PATH)
    if text in cache:
        return cache[text]

    email = get_env("MYMEMORY_EMAIL")
    kwargs = {"email": email} if email else {}
    try:
        translated = MyMemoryTranslator(source="en-US", target="ja-JP", **kwargs).translate(text)
    except Exception as exc:
        print(f"translation failed for {text[:40]!r}: {exc}")
        return None
    if not translated:
        return None

    cache[text] = translated
    _save_cache(_TITLE_CACHE_PATH, cache)
    return translated


def _short_excerpt(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cut = text.rfind(". ", 0, max_chars)
    return text[: cut + 1] if cut > 0 else text[:max_chars]


def business_summary_ja(ticker: str, summary_en: str | None) -> str | None:
    """Translated 1-2 sentence business description, cached permanently per ticker
    (a company's line of business rarely changes, unlike news headlines)."""
    cache = _load_cache(_BUSINESS_SUMMARY_CACHE_PATH)
    if ticker in cache:
        return cache[ticker]
    if not summary_en:
        return None

    excerpt = _short_excerpt(summary_en, _BUSINESS_SUMMARY_EXCERPT_CHARS)
    translated = translate_to_ja(excerpt)
    if translated:
        cache[ticker] = translated
        _save_cache(_BUSINESS_SUMMARY_CACHE_PATH, cache)
    return translated
