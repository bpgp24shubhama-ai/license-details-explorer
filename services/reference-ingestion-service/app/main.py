from fastapi import FastAPI

from app.core.config import get_settings
from app.middleware.correlation import CorrelationIdMiddleware
from app.routers import health, references
from shared.exceptions.handlers import register_exception_handlers
from shared.logging.logger import configure_logging

settings = get_settings()
configure_logging(settings.service_name, settings.log_level)

app = FastAPI(
    title="Reference Ingestion Service",
    version="1.0.0",
    description="Ingests reference master data from Excel and indexes embeddings with pgvector.",
)

app.add_middleware(CorrelationIdMiddleware)
app.include_router(health.router)
app.include_router(references.router)
register_exception_handlers(app)
