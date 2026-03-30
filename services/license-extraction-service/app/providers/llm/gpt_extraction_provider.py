import json
import re
from typing import Any

import httpx

from app.core.config import LicenseExtractionSettings
from app.providers.llm.base import LLMExtractionProvider
from app.utils.retry import run_with_retry
from shared.exceptions.app_exceptions import AppException
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class GPT5MiniExtractionProvider(LLMExtractionProvider):
    EXPECTED_FIELDS = [
        "license_number",
        "license_name",
        "license_category",
        "issuing_authority",
        "holder_name",
        "address",
        "location",
        "issue_date",
        "expiry_date",
        "validity_status",
        "confidence_score",
        "extraction_notes",
        "source_snippets",
    ]

    def __init__(self, settings: LicenseExtractionSettings) -> None:
        self._settings = settings

    def _default_payload(self) -> dict[str, Any]:
        payload = {key: None for key in self.EXPECTED_FIELDS}
        payload["source_snippets"] = []
        return payload

    def _coerce_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self._default_payload()
        for field in self.EXPECTED_FIELDS:
            if field in payload:
                result[field] = payload[field]

        snippets = result.get("source_snippets")
        if not isinstance(snippets, list):
            result["source_snippets"] = []

        return result

    @staticmethod
    def _extract_json_content(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1).strip()

        return json.loads(cleaned)

    def _fallback_extract(self, text: str) -> dict[str, Any]:
        payload = self._default_payload()

        license_no_match = re.search(
            r"(?:license\s*(?:no\.?|number)?\s*[:\-]?\s*)([A-Za-z0-9\-/]{4,})",
            text,
            flags=re.IGNORECASE,
        )
        if license_no_match:
            payload["license_number"] = license_no_match.group(1)

        issue_date_match = re.search(
            r"(?:issue\s*date\s*[:\-]?\s*)(\d{2,4}[\-/]\d{1,2}[\-/]\d{1,4})",
            text,
            flags=re.IGNORECASE,
        )
        if issue_date_match:
            payload["issue_date"] = issue_date_match.group(1)

        expiry_date_match = re.search(
            r"(?:expiry\s*date\s*[:\-]?\s*)(\d{2,4}[\-/]\d{1,2}[\-/]\d{1,4})",
            text,
            flags=re.IGNORECASE,
        )
        if expiry_date_match:
            payload["expiry_date"] = expiry_date_match.group(1)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        payload["source_snippets"] = lines[:3]
        payload["extraction_notes"] = "Fallback extraction used due to unavailable LLM API"
        payload["confidence_score"] = 0.4
        return payload

    async def _remote_extract(self, text: str, document_type: str | None = None) -> dict[str, Any]:
        prompt = (
            "Extract structured fields from the license text. "
            "Return valid JSON only with exactly these keys: "
            "license_number, license_name, license_category, issuing_authority, holder_name, "
            "address, location, issue_date, expiry_date, validity_status, confidence_score, "
            "extraction_notes, source_snippets. "
            "Use null for unknown values and never guess. "
            "Response language must be English."
        )

        if document_type:
            prompt += f" Document type hint: {document_type}."

        payload = {
            "model": self._settings.extraction_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You extract structured data from licenses. Return JSON only.",
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nLicense text:\n{text}",
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async def _call() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._extract_json_content(content)

        return await run_with_retry(
            _call,
            attempts=self._settings.external_api_retry_count,
            base_seconds=self._settings.external_api_retry_backoff_seconds,
        )

    async def extract_fields(self, text: str, document_type: str | None = None) -> dict[str, Any]:
        if not text.strip():
            raise AppException(
                status_code=422,
                code="empty_text",
                detail="Cannot extract structured data from empty text",
            )

        try:
            if self._settings.openai_api_key:
                payload = await self._remote_extract(text=text, document_type=document_type)
            else:
                payload = self._fallback_extract(text)
            return self._coerce_payload(payload)
        except json.JSONDecodeError as exc:
            logger.exception("Invalid JSON returned by extraction provider")
            raise AppException(
                status_code=502,
                code="invalid_llm_json",
                detail="Extraction model returned invalid JSON",
            ) from exc
