from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.providers.llm.gpt_embedding_provider import GPTEmbeddingProvider
from app.providers.llm.gpt_extraction_provider import GPT5MiniExtractionProvider
from app.providers.ocr.factory import OCRProviderFactory
from app.providers.translation.gpt_translation_provider import GPTTranslationProvider
from app.repositories.audit_repository import AuditRepository
from app.repositories.reference_repository import ReferenceRepository
from app.services.extraction_orchestrator import ExtractionOrchestrator
from app.services.mapping_service import MappingService
from app.services.pdf_service import PDFService
from app.services.translation_service import TranslationService


async def get_extraction_orchestrator(
    session: AsyncSession = Depends(get_db_session),
) -> ExtractionOrchestrator:
    settings = get_settings()

    pdf_service = PDFService()
    ocr_factory = OCRProviderFactory(settings)

    extraction_provider = GPT5MiniExtractionProvider(settings)
    translation_provider = GPTTranslationProvider(settings)
    translation_service = TranslationService(translation_provider)

    embedding_provider = GPTEmbeddingProvider(settings)
    reference_repository = ReferenceRepository(session)
    mapping_service = MappingService(
        settings=settings,
        reference_repository=reference_repository,
        embedding_provider=embedding_provider,
    )

    audit_repository = AuditRepository(session=session, service_name=settings.service_name)

    return ExtractionOrchestrator(
        settings=settings,
        pdf_service=pdf_service,
        ocr_factory=ocr_factory,
        extraction_provider=extraction_provider,
        translation_service=translation_service,
        mapping_service=mapping_service,
        audit_repository=audit_repository,
    )
