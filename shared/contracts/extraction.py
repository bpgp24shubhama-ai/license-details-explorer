from typing import Optional

from pydantic import BaseModel, Field


class ExtractedLicenseData(BaseModel):
    license_number: Optional[str] = None
    license_name: Optional[str] = None
    license_category: Optional[str] = None
    mapped_license_category: Optional[str] = None
    mapped_license_category_similarity: Optional[float] = None
    issuing_authority: Optional[str] = None
    holder_name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    mapped_location: Optional[str] = None
    mapped_location_similarity: Optional[float] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    validity_status: Optional[str] = None
    source_language: Optional[str] = None
    translated_to_english: bool = True
    confidence_score: Optional[float] = None
    raw_text: Optional[str] = None
    extraction_notes: Optional[str] = None
    page_numbers: list[int] = Field(default_factory=list)
    source_snippets: list[str] = Field(default_factory=list)
    request_id: str
    ocr_used: bool
    ocr_provider: Optional[str] = None
    extraction_model: str
    processing_time_ms: int
    document_type: Optional[str] = None
