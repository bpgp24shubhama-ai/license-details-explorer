from fastapi import FastAPI

from app.core.config import get_settings
from app.middleware.correlation import CorrelationIdMiddleware
from app.routers import extraction, health
from shared.exceptions.handlers import register_exception_handlers
from shared.logging.logger import configure_logging

settings = get_settings()
configure_logging(settings.service_name, settings.log_level)

app = FastAPI(
    title="License Extraction Service",
    version="1.0.0",
    description="Extracts structured data from commercial license PDFs.",
)

app.add_middleware(CorrelationIdMiddleware)
app.include_router(health.router)
app.include_router(extraction.router)
register_exception_handlers(app)
