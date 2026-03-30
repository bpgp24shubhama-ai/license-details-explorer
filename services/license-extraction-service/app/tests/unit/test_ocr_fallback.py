import pytest

from app.services.extraction_orchestrator import ExtractionOrchestrator
from app.services.pdf_service import PageText


class FakeSettings:
    extraction_model = "gpt-5-mini"


class FakePDFService:
    def extract_page_texts(self, _: bytes) -> list[PageText]:
        return [PageText(page_number=1, text=""), PageText(page_number=2, text="Native text")]

    def render_pages_to_images(self, _: bytes) -> list[bytes]:
        return [b"img1", b"img2"]

    @staticmethod
    def merge_page_texts(page_texts: list[PageText]) -> str:
        return "\n".join(page.text for page in page_texts)


class FakeOCRProvider:
    async def extract_text(self, page_images: list[bytes]):
        assert page_images == [b"img1"]

        class Result:
            page_number = 1
            text = "OCR text"

        return [Result()]


class FakeOCRFactory:
    def get_provider(self, _: str):
        return FakeOCRProvider()


class FakeExtractionProvider:
    async def extract_fields(self, text: str, document_type: str | None = None):
        assert "OCR text" in text
        return {
            "license_number": "ABC123",
            "license_name": None,
            "license_category": "Food",
            "issuing_authority": None,
            "holder_name": None,
            "address": None,
            "location": "Mumabi",
            "issue_date": None,
            "expiry_date": None,
            "validity_status": None,
            "confidence_score": 0.8,
            "extraction_notes": None,
            "source_snippets": [],
        }


class FakeTranslationService:
    async def to_english(self, text: str):
        return "en", text, True


class FakeMappingService:
    async def map_value(self, reference_type: str, value: str | None):
        if reference_type == "license_category":
            return "FSSAI", 0.9
        if reference_type == "location":
            return "Mumbai", 0.95
        return None, None


class FakeAuditRepository:
    async def record_processing(self, **kwargs):
        assert kwargs["status"] in {"success", "failed"}

    async def save_extraction_history(self, payload: dict):
        assert "request_id" in payload


@pytest.mark.asyncio
async def test_orchestrator_uses_ocr_for_blank_pages():
    orchestrator = ExtractionOrchestrator(
        settings=FakeSettings(),
        pdf_service=FakePDFService(),
        ocr_factory=FakeOCRFactory(),
        extraction_provider=FakeExtractionProvider(),
        translation_service=FakeTranslationService(),
        mapping_service=FakeMappingService(),
        audit_repository=FakeAuditRepository(),
    )

    result = await orchestrator.extract_from_pdf(
        pdf_bytes=b"fake",
        ocr_provider="pytesseract",
        document_type="fssai",
    )

    assert result.ocr_used is True
    assert result.mapped_location == "Mumbai"
    assert result.license_number == "ABC123"
