import asyncio
from io import BytesIO

import pytesseract
from PIL import Image

from app.core.config import LicenseExtractionSettings
from app.providers.ocr.base import OCRPageResult, OCRProvider


class PytesseractOCRProvider(OCRProvider):
    provider_name = "pytesseract"

    def __init__(self, settings: LicenseExtractionSettings) -> None:
        self._settings = settings
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    @staticmethod
    def _extract_sync(page_number: int, image_bytes: bytes) -> OCRPageResult:
        with Image.open(BytesIO(image_bytes)) as image:
            text = pytesseract.image_to_string(image)
        return OCRPageResult(page_number=page_number, text=text.strip())

    async def extract_text(self, page_images: list[bytes]) -> list[OCRPageResult]:
        tasks = [
            asyncio.to_thread(self._extract_sync, idx + 1, image)
            for idx, image in enumerate(page_images)
        ]
        return await asyncio.gather(*tasks)
