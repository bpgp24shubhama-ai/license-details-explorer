import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExtractionHistory, ProcessingAudit


class AuditRepository:
    def __init__(self, session: AsyncSession, service_name: str) -> None:
        self._session = session
        self._service_name = service_name

    async def record_processing(
        self,
        request_id: str,
        status: str,
        processing_time_ms: int,
        payload: dict[str, Any],
    ) -> None:
        row = ProcessingAudit(
            request_id=uuid.UUID(request_id),
            service_name=self._service_name,
            status=status,
            processing_time_ms=processing_time_ms,
            payload=payload,
        )
        self._session.add(row)
        await self._session.commit()

    async def save_extraction_history(self, payload: dict[str, Any]) -> None:
        row = ExtractionHistory(
            request_id=uuid.UUID(payload["request_id"]),
            document_type=payload.get("document_type"),
            extracted_json=payload,
            source_language=payload.get("source_language"),
            ocr_used=bool(payload.get("ocr_used", False)),
            ocr_provider=payload.get("ocr_provider"),
            extraction_model=payload.get("extraction_model"),
            processing_time_ms=payload.get("processing_time_ms"),
        )
        self._session.add(row)
        await self._session.commit()
