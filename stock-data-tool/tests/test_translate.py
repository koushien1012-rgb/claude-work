import json
from unittest.mock import MagicMock, patch

import translate as mod


def test_translate_to_ja_returns_translation_and_caches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = MagicMock()
    fake.translate.return_value = "テスト訳文"
    with patch.object(mod, "MyMemoryTranslator", return_value=fake) as ctor:
        result = mod.translate_to_ja("Test headline")

    assert result == "テスト訳文"
    cache = json.loads((tmp_path / "output/cache/translation_cache.json").read_text(encoding="utf-8"))
    assert cache["Test headline"] == "テスト訳文"

    # second call must hit the cache, not the translator again
    with patch.object(mod, "MyMemoryTranslator", return_value=fake) as ctor2:
        result2 = mod.translate_to_ja("Test headline")
    assert result2 == "テスト訳文"
    ctor2.assert_not_called()


def test_translate_to_ja_returns_none_for_empty_text():
    assert mod.translate_to_ja("") is None
    assert mod.translate_to_ja(None) is None


def test_translate_to_ja_returns_none_and_does_not_raise_on_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = MagicMock()
    fake.translate.side_effect = RuntimeError("quota exceeded")
    with patch.object(mod, "MyMemoryTranslator", return_value=fake):
        result = mod.translate_to_ja("Some headline")
    assert result is None


def test_business_summary_ja_translates_short_excerpt_and_caches_by_ticker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = MagicMock()
    fake.translate.return_value = "日本語の要約"
    long_summary = "First sentence about the company. " + ("Filler detail. " * 50)
    with patch.object(mod, "MyMemoryTranslator", return_value=fake) as ctor:
        result = mod.business_summary_ja("TEST", long_summary)

    assert result == "日本語の要約"
    # the excerpt passed to the translator must be trimmed, not the full ~800+ char summary
    translated_arg = fake.translate.call_args[0][0]
    assert len(translated_arg) <= mod._BUSINESS_SUMMARY_EXCERPT_CHARS

    cache = json.loads((tmp_path / "output/cache/business_summary_ja.json").read_text(encoding="utf-8"))
    assert cache["TEST"] == "日本語の要約"

    # second call for the same ticker must hit the cache, no translator call at all
    with patch.object(mod, "MyMemoryTranslator", return_value=fake) as ctor2:
        result2 = mod.business_summary_ja("TEST", long_summary)
    assert result2 == "日本語の要約"
    ctor2.assert_not_called()


def test_business_summary_ja_returns_none_when_no_summary_available(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert mod.business_summary_ja("TEST", None) is None
