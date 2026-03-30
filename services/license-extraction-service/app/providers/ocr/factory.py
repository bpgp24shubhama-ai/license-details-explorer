from app.core.config import LicenseExtractionSettings
from app.providers.ocr.base import OCRProvider
from app.providers.ocr.gemma_ocr_provider import GemmaOCRProvider
from app.providers.ocr.gpt_ocr_provider import GPT5MiniOCRProvider
from app.providers.ocr.pytesseract_provider import PytesseractOCRProvider
from shared.exceptions.app_exceptions import AppException


class OCRProviderFactory:
    def __init__(self, settings: LicenseExtractionSettings) -> None:
        self._settings = settings

    def get_provider(self, provider_name: str) -> OCRProvider:
        normalized_name = provider_name.strip().lower()
        if normalized_name == "pytesseract":
            return PytesseractOCRProvider(self._settings)
        if normalized_name in {"gpt-5-mini", "gpt_5_mini"}:
            return GPT5MiniOCRProvider(self._settings)
        if normalized_name in {"gemma-3-4b", "gemma", "gemma_3_4b"}:
            return GemmaOCRProvider(self._settings)

        raise AppException(
            status_code=400,
            code="unsupported_ocr_provider",
            detail=f"Unsupported OCR provider: {provider_name}",
        )
