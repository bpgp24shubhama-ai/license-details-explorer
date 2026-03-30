import pytest

from app.services.translation_service import TranslationService


class FakeTranslator:
    def __init__(self) -> None:
        self.called = False

    async def translate_to_english(self, text: str) -> str:
        self.called = True
        return f"EN::{text}"


@pytest.mark.asyncio
async def test_translation_service_translates_non_english(monkeypatch):
    translator = FakeTranslator()
    service = TranslationService(translator)

    monkeypatch.setattr(TranslationService, "detect_language", staticmethod(lambda _: "es"))

    source_lang, translated, success = await service.to_english("hola")

    assert source_lang == "es"
    assert translated == "EN::hola"
    assert success is True
    assert translator.called is True


@pytest.mark.asyncio
async def test_translation_service_skips_english(monkeypatch):
    translator = FakeTranslator()
    service = TranslationService(translator)

    monkeypatch.setattr(TranslationService, "detect_language", staticmethod(lambda _: "en"))

    source_lang, translated, success = await service.to_english("hello")

    assert source_lang == "en"
    assert translated == "hello"
    assert success is True
    assert translator.called is False


@pytest.mark.asyncio
async def test_translation_service_marks_failure_when_non_english_not_translated(monkeypatch):
    translator = FakeTranslator()
    service = TranslationService(translator)

    async def no_change_translate(text: str) -> str:
        return text

    translator.translate_to_english = no_change_translate
    monkeypatch.setattr(TranslationService, "detect_language", staticmethod(lambda _: "es"))

    source_lang, translated, success = await service.to_english("hola")

    assert source_lang == "es"
    assert translated == "hola"
    assert success is False
