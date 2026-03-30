from langdetect import LangDetectException, detect

from app.providers.translation.base import TranslationProvider


class TranslationService:
    def __init__(self, provider: TranslationProvider) -> None:
        self._provider = provider

    @staticmethod
    def detect_language(text: str) -> str:
        if not text.strip():
            return "en"
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    async def to_english(self, text: str) -> tuple[str, str, bool]:
        source_language = self.detect_language(text)

        if source_language == "en":
            return source_language, text, True

        translated = await self._provider.translate_to_english(text)
        translated_to_english = bool(translated.strip()) and translated.strip() != text.strip()
        return source_language, translated, translated_to_english
