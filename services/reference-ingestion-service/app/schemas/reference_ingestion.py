from enum import Enum

from pydantic import BaseModel

from shared.contracts.reference import LookupValidationResponse, ReferenceIngestionResult


class IngestionMode(str, Enum):
    reload = "reload"
    upsert = "upsert"


class ReindexRequest(BaseModel):
    reference_type: str


class ValidationRequest(BaseModel):
    reference_type: str
    value: str


class IngestionResponse(ReferenceIngestionResult):
    pass


class ValidationResponse(LookupValidationResponse):
    pass
