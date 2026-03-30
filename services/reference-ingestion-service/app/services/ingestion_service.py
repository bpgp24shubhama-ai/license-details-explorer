import time
import uuid

from app.core.config import ReferenceIngestionSettings
from app.providers.llm.base import EmbeddingProvider
from app.repositories.audit_repository import AuditRepository
from app.repositories.reference_repository import ReferenceRepository
from app.services.excel_service import ExcelService
from shared.contracts.reference import ReferenceIngestionResult, ReferenceRecord
from shared.exceptions.app_exceptions import AppException


class ReferenceIngestionService:
    def __init__(
        self,
        settings: ReferenceIngestionSettings,
        excel_service: ExcelService,
        embedding_provider: EmbeddingProvider,
        reference_repository: ReferenceRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self._settings = settings
        self._excel_service = excel_service
        self._embedding_provider = embedding_provider
        self._reference_repository = reference_repository
        self._audit_repository = audit_repository

    @staticmethod
    def normalize_value(value: str) -> str:
        return " ".join(value.strip().lower().split())

    async def ingest_excel(
        self,
        file_bytes: bytes,
        reference_type: str,
        mode: str,
    ) -> ReferenceIngestionResult:
        if mode not in {"reload", "upsert"}:
            raise AppException(
                status_code=400,
                code="invalid_mode",
                detail="Mode must be either reload or upsert",
            )

        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()

        try:
            rows, invalid_rows = self._excel_service.parse_reference_rows(file_bytes)
            normalized_values = [self.normalize_value(row["raw_value"]) for row in rows]
            embeddings = await self._embedding_provider.embed_texts(normalized_values)

            if len(embeddings) != len(rows):
                raise AppException(
                    status_code=502,
                    code="embedding_mismatch",
                    detail="Embedding provider returned inconsistent result size",
                )

            existing_values: set[str] = set()
            if mode == "reload":
                await self._reference_repository.reload_reference_type(reference_type)
            else:
                existing_values = await self._reference_repository.get_existing_normalized(
                    reference_type=reference_type,
                    normalized_values=normalized_values,
                )

            records: list[ReferenceRecord] = []
            for index, row in enumerate(rows):
                records.append(
                    ReferenceRecord(
                        reference_type=reference_type,
                        raw_value=row["raw_value"],
                        normalized_value=normalized_values[index],
                        embedding=embeddings[index],
                        metadata_json=row["metadata_json"],
                    )
                )

            await self._reference_repository.bulk_upsert(records)

            if mode == "reload":
                inserted_rows = len(records)
                updated_rows = 0
            else:
                inserted_rows = sum(1 for value in normalized_values if value not in existing_values)
                updated_rows = len(records) - inserted_rows

            processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            response = ReferenceIngestionResult(
                request_id=request_id,
                reference_type=reference_type,
                mode=mode,
                processed_rows=len(rows) + invalid_rows,
                inserted_rows=inserted_rows,
                updated_rows=updated_rows,
                invalid_rows=invalid_rows,
            )

            await self._audit_repository.record_processing(
                request_id=request_id,
                status="success",
                processing_time_ms=processing_time_ms,
                payload=response.model_dump(mode="json"),
            )
            return response

        except Exception as exc:
            processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            try:
                await self._audit_repository.record_processing(
                    request_id=request_id,
                    status="failed",
                    processing_time_ms=processing_time_ms,
                    payload={"error": str(exc), "reference_type": reference_type, "mode": mode},
                )
            except Exception:
                pass

            if isinstance(exc, AppException):
                raise

            raise AppException(
                status_code=500,
                code="ingestion_failed",
                detail="Reference ingestion failed",
            ) from exc

    async def reindex_reference_type(self, reference_type: str) -> ReferenceIngestionResult:
        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()

        try:
            rows = await self._reference_repository.list_by_type(reference_type)
            if not rows:
                raise AppException(
                    status_code=404,
                    code="reference_type_not_found",
                    detail=f"No records found for reference_type={reference_type}",
                )

            normalized_values = [row.normalized_value for row in rows]
            embeddings = await self._embedding_provider.embed_texts(normalized_values)

            records = [
                ReferenceRecord(
                    reference_type=row.reference_type,
                    raw_value=row.raw_value,
                    normalized_value=row.normalized_value,
                    embedding=embeddings[index],
                    metadata_json=row.metadata_json,
                )
                for index, row in enumerate(rows)
            ]
            await self._reference_repository.bulk_upsert(records)

            processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            response = ReferenceIngestionResult(
                request_id=request_id,
                reference_type=reference_type,
                mode="reindex",
                processed_rows=len(records),
                inserted_rows=0,
                updated_rows=len(records),
                invalid_rows=0,
            )
            await self._audit_repository.record_processing(
                request_id=request_id,
                status="success",
                processing_time_ms=processing_time_ms,
                payload=response.model_dump(mode="json"),
            )
            return response

        except Exception as exc:
            processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            try:
                await self._audit_repository.record_processing(
                    request_id=request_id,
                    status="failed",
                    processing_time_ms=processing_time_ms,
                    payload={"error": str(exc), "reference_type": reference_type, "mode": "reindex"},
                )
            except Exception:
                pass

            if isinstance(exc, AppException):
                raise

            raise AppException(
                status_code=500,
                code="reindex_failed",
                detail="Reference reindex failed",
            ) from exc
