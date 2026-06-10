"""Logging configuration for MnemOS."""

from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logging for the application.

    Args:
        level: Log level name (DEBUG, INFO, WARNING, ERROR).
    """
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=_LOG_FORMAT)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
