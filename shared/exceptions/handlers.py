from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from shared.exceptions.app_exceptions import AppException
from shared.logging.logger import get_correlation_id, get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "detail": exc.detail,
                "correlation_id": get_correlation_id(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "detail": exc.errors(),
                "correlation_id": get_correlation_id(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", extra={"error": str(exc)})
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_server_error",
                "detail": "Unexpected server error",
                "correlation_id": get_correlation_id(),
            },
        )
