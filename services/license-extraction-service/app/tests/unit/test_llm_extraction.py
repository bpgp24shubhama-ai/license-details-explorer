import pytest

from app.core.config import LicenseExtractionSettings
from app.providers.llm.gpt_extraction_provider import GPT5MiniExtractionProvider


@pytest.mark.asyncio
async def test_llm_extraction_fallback_returns_json_fields():
    settings = LicenseExtractionSettings(OPENAI_API_KEY="")
    provider = GPT5MiniExtractionProvider(settings)

    payload = await provider.extract_fields(
        "License Number: LIC-12345\nIssue Date: 2024-01-01\nExpiry Date: 2029-01-01"
    )

    assert payload["license_number"] == "LIC-12345"
    assert payload["issue_date"] == "2024-01-01"
    assert payload["expiry_date"] == "2029-01-01"
    assert isinstance(payload["source_snippets"], list)


def test_extract_json_content_from_fenced_json():
    content = "```json\n{\"license_number\": \"A1\"}\n```"
    parsed = GPT5MiniExtractionProvider._extract_json_content(content)
    assert parsed["license_number"] == "A1"
