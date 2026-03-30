from fastapi.testclient import TestClient

from app.api.deps import get_extraction_orchestrator
from app.main import app
from shared.contracts.extraction import ExtractedLicenseData


class FakeOrchestrator:
    async def extract_from_pdf(self, pdf_bytes: bytes, ocr_provider: str, document_type: str | None):
        assert pdf_bytes.startswith(b"%PDF")
        return ExtractedLicenseData(
            license_number="LIC-1",
            license_name="Shop License",
            license_category="Shop",
            mapped_license_category="Shop License",
            mapped_license_category_similarity=0.9,
            issuing_authority=None,
            holder_name=None,
            address=None,
            location="Mumabi",
            mapped_location="Mumbai",
            mapped_location_similarity=0.96,
            issue_date=None,
            expiry_date=None,
            validity_status=None,
            source_language="en",
            translated_to_english=True,
            confidence_score=0.9,
            raw_text="dummy",
            extraction_notes=None,
            page_numbers=[1],
            source_snippets=[],
            request_id="3eeb641f-f20f-4172-b2ba-cf42f4f0804e",
            ocr_used=False,
            ocr_provider=ocr_provider,
            extraction_model="gpt-5-mini",
            processing_time_ms=10,
            document_type=document_type,
        )


def test_extract_endpoint_returns_structured_json():
    app.dependency_overrides[get_extraction_orchestrator] = lambda: FakeOrchestrator()

    client = TestClient(app)
    response = client.post(
        "/api/v1/extractions",
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"ocr_provider": "pytesseract", "document_type": "shop"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["license_number"] == "LIC-1"
    assert payload["mapped_location"] == "Mumbai"
    assert payload["document_type"] == "shop"

    app.dependency_overrides.clear()
