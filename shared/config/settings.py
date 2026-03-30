from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    env: str = Field(default="dev", alias="ENV")
    service_name: str = Field(default="service", alias="SERVICE_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/bmls",
        alias="DATABASE_URL",
    )

    request_timeout_seconds: int = Field(default=30, alias="REQUEST_TIMEOUT_SECONDS")
    external_api_retry_count: int = Field(default=3, alias="EXTERNAL_API_RETRY_COUNT")
    external_api_retry_backoff_seconds: int = Field(
        default=1,
        alias="EXTERNAL_API_RETRY_BACKOFF_SECONDS",
    )

    similarity_threshold: float = Field(default=0.70, alias="SIMILARITY_THRESHOLD")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    extraction_model: str = Field(default="gpt-5-mini", alias="EXTRACTION_MODEL")
    ocr_model: str = Field(default="gpt-5-mini", alias="OCR_MODEL")
    translation_model: str = Field(default="gpt-5-mini", alias="TRANSLATION_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

    default_ocr_provider: str = Field(default="pytesseract", alias="DEFAULT_OCR_PROVIDER")
    tesseract_cmd: str = Field(default="/usr/bin/tesseract", alias="TESSERACT_CMD")
