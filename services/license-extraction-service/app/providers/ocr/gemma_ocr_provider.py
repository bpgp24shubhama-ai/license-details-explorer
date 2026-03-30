import base64

import httpx

from app.core.config import LicenseExtractionSettings
from app.providers.ocr.base import OCRPageResult, OCRProvider
from app.utils.retry import run_with_retry
from shared.exceptions.app_exceptions import AppException


class GemmaOCRProvider(OCRProvider):
    provider_name = "gemma-3-4b"

    def __init__(self, settings: LicenseExtractionSettings) -> None:
        self._settings = settings

    async def _extract_single_page(self, page_number: int, image_bytes: bytes) -> OCRPageResult:
        if not self._settings.openai_api_key:
            raise AppException(
                status_code=503,
                code="ocr_provider_unavailable",
                detail="OPENAI_API_KEY is required for gemma OCR provider",
            )

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": "gemma-3-4b-it",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an OCR engine. Return text only.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all visible text from this image and return plain text only.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_image}",
                            },
                        },
                    ],
                },
            ],
            "temperature": 0,
        }

        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async def _call() -> OCRPageResult:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"].strip()
                return OCRPageResult(page_number=page_number, text=text)

        return await run_with_retry(
            _call,
            attempts=self._settings.external_api_retry_count,
            base_seconds=self._settings.external_api_retry_backoff_seconds,
        )

    async def extract_text(self, page_images: list[bytes]) -> list[OCRPageResult]:
        results: list[OCRPageResult] = []
        for idx, image in enumerate(page_images):
            results.append(await self._extract_single_page(page_number=idx + 1, image_bytes=image))
        return results
