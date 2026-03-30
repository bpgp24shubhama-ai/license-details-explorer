import httpx

from app.core.config import LicenseExtractionSettings
from app.providers.translation.base import TranslationProvider
from app.utils.retry import run_with_retry


class GPTTranslationProvider(TranslationProvider):
    def __init__(self, settings: LicenseExtractionSettings) -> None:
        self._settings = settings

    async def _remote_translate(self, text: str) -> str:
        payload = {
            "model": self._settings.translation_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Translate content to English. Return plain text only.",
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            "temperature": 0,
        }

        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async def _call() -> str:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

        return await run_with_retry(
            _call,
            attempts=self._settings.external_api_retry_count,
            base_seconds=self._settings.external_api_retry_backoff_seconds,
        )

    async def translate_to_english(self, text: str) -> str:
        if not text.strip() or not self._settings.openai_api_key:
            return text
        return await self._remote_translate(text)
