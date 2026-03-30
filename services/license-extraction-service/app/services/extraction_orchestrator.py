import time
import uuid

from app.core.config import LicenseExtractionSettings
from app.providers.llm.base import LLMExtractionProvider
from app.providers.ocr.factory import OCRProviderFactory
from app.repositories.audit_repository import AuditRepository
from app.services.mapping_service import MappingService
from app.services.pdf_service import PDFService, PageText
from app.services.translation_service import TranslationService
from shared.contracts.extraction import ExtractedLicenseData
from shared.exceptions.app_exceptions import AppException


class ExtractionOrchestrator:
    def __init__(
        self,
        settings: LicenseExtractionSettings,
        pdf_service: PDFService,
        ocr_factory: OCRProviderFactory,
        extraction_provider: LLMExtractionProvider,
        translation_service: TranslationService,
        mapping_service: MappingService,
        audit_repository: AuditRepository,
    ) -> None:
        self._settings = settings
        self._pdf_service = pdf_service
        self._ocr_factory = ocr_factory
        self._extraction_provider = extraction_provider
        self._translation_service = translation_service
        self._mapping_service = mapping_service
        self._audit_repository = audit_repository

    async def extract_from_pdf(
        self,
        pdf_bytes: bytes,
        ocr_provider: str,
        document_type: str | None,
    ) -> ExtractedLicenseData:
        if not pdf_bytes:
            raise AppException(status_code=400, code="empty_pdf", detail="Uploaded PDF is empty")

        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()

        try:
            native_pages = self._pdf_service.extract_page_texts(pdf_bytes)
            if not native_pages:
                raise AppException(
                    status_code=422,
                    code="invalid_pdf",
                    detail="Unable to read any pages from PDF",
                )

            merged_pages: list[PageText] = []
            missing_indexes: list[int] = [
                idx for idx, page in enumerate(native_pages) if not page.text.strip()
            ]
            ocr_used = len(missing_indexes) > 0

            if ocr_used:
                page_images = self._pdf_service.render_pages_to_images(pdf_bytes)
                provider = self._ocr_factory.get_provider(ocr_provider)
                ocr_images = [page_images[idx] for idx in missing_indexes]
                ocr_results = await provider.extract_text(ocr_images)
                ocr_by_page = {
                    missing_indexes[idx] + 1: result.text for idx, result in enumerate(ocr_results)
                }
            else:
                ocr_by_page = {}

            for idx, native_page in enumerate(native_pages):
                page_number = idx + 1
                fallback_text = ocr_by_page.get(page_number, "")
                page_text = native_page.text if native_page.text.strip() else fallback_text
                merged_pages.append(PageText(page_number=page_number, text=page_text.strip()))

            raw_text = self._pdf_service.merge_page_texts(merged_pages)
            if not raw_text.strip():
                raise AppException(
                    status_code=422,
                    code="no_text_extracted",
                    detail="No readable text could be extracted from PDF",
                )

            source_language, english_text, translated_to_english = await self._translation_service.to_english(raw_text)
            if source_language != "en" and not translated_to_english:
                raise AppException(
                    status_code=502,
                    code="translation_failed",
                    detail="Source text is non-English and translation to English failed",
                )

            if not english_text.strip():
                raise AppException(
                    status_code=502,
                    code="translation_empty",
                    detail="Translation produced empty text",
                )

            extracted_fields = await self._extraction_provider.extract_fields(
                text=english_text,
                document_type=document_type,
            )

            mapped_license_category, category_similarity = await self._mapping_service.map_value(
                reference_type="license_category",
                value=extracted_fields.get("license_category"),
            )
            mapped_location, location_similarity = await self._mapping_service.map_value(
                reference_type="location",
                value=extracted_fields.get("location"),
            )

            confidence_score = extracted_fields.get("confidence_score")
            processing_time_ms = int((time.perf_counter() - started_at) * 1000)

            response = ExtractedLicenseData(
                license_number=extracted_fields.get("license_number"),
                license_name=extracted_fields.get("license_name"),
                license_category=extracted_fields.get("license_category"),
                mapped_license_category=mapped_license_category,
                mapped_license_category_similarity=category_similarity,
                issuing_authority=extracted_fields.get("issuing_authority"),
                holder_name=extracted_fields.get("holder_name"),
                address=extracted_fields.get("address"),
                location=extracted_fields.get("location"),
                mapped_location=mapped_location,
                mapped_location_similarity=location_similarity,
                issue_date=extracted_fields.get("issue_date"),
                expiry_date=extracted_fields.get("expiry_date"),
                validity_status=extracted_fields.get("validity_status"),
                source_language=source_language,
                translated_to_english=translated_to_english,
                confidence_score=float(confidence_score) if confidence_score is not None else None,
                raw_text=raw_text,
                extraction_notes=extracted_fields.get("extraction_notes"),
                page_numbers=[page.page_number for page in merged_pages if page.text.strip()],
                source_snippets=[str(item) for item in extracted_fields.get("source_snippets", [])],
                request_id=request_id,
                ocr_used=ocr_used,
                ocr_provider=ocr_provider,
                extraction_model=self._settings.extraction_model,
                processing_time_ms=processing_time_ms,
                document_type=document_type,
            )

            payload = response.model_dump(mode="json")
            await self._audit_repository.record_processing(
                request_id=request_id,
                status="success",
                processing_time_ms=processing_time_ms,
                payload=payload,
            )
            await self._audit_repository.save_extraction_history(payload)
            return response

        except Exception as exc:
            processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            try:
                await self._audit_repository.record_processing(
                    request_id=request_id,
                    status="failed",
                    processing_time_ms=processing_time_ms,
                    payload={"error": str(exc), "document_type": document_type},
                )
            except Exception:
                pass

            if isinstance(exc, AppException):
                raise

            raise AppException(
                status_code=500,
                code="extraction_failed",
                detail="Extraction pipeline failed",
            ) from exc
