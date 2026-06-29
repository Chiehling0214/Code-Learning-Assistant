"""Structured JSON logging configuration."""

import logging
import sys

from pythonjsonlogger import json as jsonlogger

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger to emit single-line JSON records.

    Idempotent: safe to call more than once (e.g. app start + reloads).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Align uvicorn loggers with our handler instead of their default formatters.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
