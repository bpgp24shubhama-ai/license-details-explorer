from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_lookup_validation_service, get_reference_ingestion_service
from app.schemas.reference_ingestion import (
    IngestionMode,
    IngestionResponse,
    ReindexRequest,
    ValidationRequest,
    ValidationResponse,
)
from app.services.ingestion_service import ReferenceIngestionService
from app.services.validation_service import LookupValidationService
from shared.exceptions.app_exceptions import AppException

router = APIRouter(prefix="/api/v1/references", tags=["references"])


@router.post("/upload", response_model=IngestionResponse)
async def upload_references(
    file: UploadFile = File(...),
    reference_type: str = Form(...),
    mode: IngestionMode = Form(default=IngestionMode.upsert),
    ingestion_service: ReferenceIngestionService = Depends(get_reference_ingestion_service),
) -> IngestionResponse:
    allowed_types = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
    }
    if file.content_type not in allowed_types:
        raise AppException(
            status_code=400,
            code="unsupported_file_type",
            detail="Only Excel files are supported",
        )

    file_bytes = await file.read()
    return await ingestion_service.ingest_excel(
        file_bytes=file_bytes,
        reference_type=reference_type,
        mode=mode.value,
    )


@router.post("/reindex", response_model=IngestionResponse)
async def reindex_references(
    request: ReindexRequest,
    ingestion_service: ReferenceIngestionService = Depends(get_reference_ingestion_service),
) -> IngestionResponse:
    return await ingestion_service.reindex_reference_type(request.reference_type)


@router.post("/validate", response_model=ValidationResponse)
async def validate_lookup(
    request: ValidationRequest,
    validation_service: LookupValidationService = Depends(get_lookup_validation_service),
) -> ValidationResponse:
    return await validation_service.validate(
        reference_type=request.reference_type,
        value=request.value,
    )
