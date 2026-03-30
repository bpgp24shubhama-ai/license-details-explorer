from functools import lru_cache

from pydantic import Field

from shared.config.settings import BaseServiceSettings


class LicenseExtractionSettings(BaseServiceSettings):
    service_name: str = Field(default="license-extraction-service", alias="SERVICE_NAME")


@lru_cache
def get_settings() -> LicenseExtractionSettings:
    return LicenseExtractionSettings()
