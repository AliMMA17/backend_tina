"""Structured logging configuration.

Decision: Use stdlib logging with a consistent format that works well
with container log aggregators (JSON-friendly, correlation-ready).
Avoid heavy frameworks unless the team already standardizes on them.
"""

import logging
import sys
from typing import Any

from src.core.config import get_settings


def setup_logging() -> None:
    """Configure root logger for the application."""
    settings = get_settings()

    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Simple, structured format suitable for both local and container logs
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if settings.is_development
        else "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.db_echo else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


def log_context(**kwargs: Any) -> dict[str, Any]:
    """Helper to build structured log context dicts."""
    return {k: v for k, v in kwargs.items() if v is not None}
