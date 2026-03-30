from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_extraction_orchestrator
from app.schemas.extraction import ExtractionResponse, OCRProviderType
from app.services.extraction_orchestrator import ExtractionOrchestrator
from shared.exceptions.app_exceptions import AppException

router = APIRouter(prefix="/api/v1", tags=["extractions"])


@router.post("/extractions", response_model=ExtractionResponse)
async def extract_license(
    file: UploadFile = File(...),
    ocr_provider: OCRProviderType = Form(default=OCRProviderType.pytesseract),
    document_type: str | None = Form(default=None),
    orchestrator: ExtractionOrchestrator = Depends(get_extraction_orchestrator),
) -> ExtractionResponse:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise AppException(
            status_code=400,
            code="unsupported_file_type",
            detail="Only PDF files are supported",
        )

    pdf_bytes = await file.read()
    return await orchestrator.extract_from_pdf(
        pdf_bytes=pdf_bytes,
        ocr_provider=ocr_provider.value,
        document_type=document_type,
    )
