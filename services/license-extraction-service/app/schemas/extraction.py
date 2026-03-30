from enum import Enum

from shared.contracts.extraction import ExtractedLicenseData


class OCRProviderType(str, Enum):
    pytesseract = "pytesseract"
    gpt_5_mini = "gpt-5-mini"
    gemma_3_4b = "gemma-3-4b"


class ExtractionResponse(ExtractedLicenseData):
    pass
