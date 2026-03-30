from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.providers.llm.gpt_embedding_provider import GPTEmbeddingProvider
from app.repositories.audit_repository import AuditRepository
from app.repositories.reference_repository import ReferenceRepository
from app.services.excel_service import ExcelService
from app.services.ingestion_service import ReferenceIngestionService
from app.services.validation_service import LookupValidationService


async def get_reference_ingestion_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReferenceIngestionService:
    settings = get_settings()
    embedding_provider = GPTEmbeddingProvider(settings)
    excel_service = ExcelService()
    reference_repository = ReferenceRepository(session)
    audit_repository = AuditRepository(session=session, service_name=settings.service_name)

    return ReferenceIngestionService(
        settings=settings,
        excel_service=excel_service,
        embedding_provider=embedding_provider,
        reference_repository=reference_repository,
        audit_repository=audit_repository,
    )


async def get_lookup_validation_service(
    session: AsyncSession = Depends(get_db_session),
) -> LookupValidationService:
    settings = get_settings()
    embedding_provider = GPTEmbeddingProvider(settings)
    reference_repository = ReferenceRepository(session)

    return LookupValidationService(
        settings=settings,
        embedding_provider=embedding_provider,
        reference_repository=reference_repository,
    )
