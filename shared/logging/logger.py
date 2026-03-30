import contextvars
import logging
from typing import Any

from pythonjsonlogger import jsonlogger


_correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id",
    default="",
)


def set_correlation_id(correlation_id: str) -> None:
    _correlation_id_ctx.set(correlation_id)


def get_correlation_id() -> str:
    return _correlation_id_ctx.get()


class CorrelationJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, service_name: str) -> None:
        super().__init__("%(asctime)s %(levelname)s %(name)s %(message)s")
        self._service_name = service_name

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = self._service_name
        log_record["correlation_id"] = get_correlation_id()


def configure_logging(service_name: str, level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.upper())

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CorrelationJsonFormatter(service_name=service_name))

    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
