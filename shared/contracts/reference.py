from typing import Any, Optional

from pydantic import BaseModel, Field


class ReferenceRecord(BaseModel):
    reference_type: str
    raw_value: str
    normalized_value: str
    embedding: list[float]
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ReferenceIngestionResult(BaseModel):
    request_id: str
    reference_type: str
    mode: str
    processed_rows: int
    inserted_rows: int
    updated_rows: int
    invalid_rows: int


class LookupValidationRequest(BaseModel):
    reference_type: str
    value: str


class LookupValidationResponse(BaseModel):
    reference_type: str
    value: str
    mapped_value: Optional[str] = None
    similarity: Optional[float] = None
