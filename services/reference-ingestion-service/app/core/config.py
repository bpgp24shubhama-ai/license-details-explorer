from functools import lru_cache

from pydantic import Field

from shared.config.settings import BaseServiceSettings


class ReferenceIngestionSettings(BaseServiceSettings):
    service_name: str = Field(default="reference-ingestion-service", alias="SERVICE_NAME")


@lru_cache
def get_settings() -> ReferenceIngestionSettings:
    return ReferenceIngestionSettings()
