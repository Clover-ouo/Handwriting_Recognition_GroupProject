"""Logging utilities for API endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from .config import Settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"  # Log format for all handlers.
MIN_SEPARATOR_LENGTH = 1  # Minimum length for log separator lines.
MIN_DECIMALS = 0  # Minimum decimal places for duration formatting.


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure and return the application logger."""
    logging.basicConfig(level=settings.log_level.upper(), format=LOG_FORMAT)
    logger = logging.getLogger(settings.app_name)
    logger.setLevel(settings.log_level.upper())
    return logger


def log_endpoint_start(logger: logging.Logger, endpoint: str, request_id: str, separator: str) -> None:
    """Log endpoint start event."""
    logger.info(separator)
    logger.info("📝 [START] endpoint=%s | request_id=%s", endpoint, request_id)
    logger.info(separator)


def log_endpoint_success(
    logger: logging.Logger,
    endpoint: str,
    request_id: str,
    duration_ms: float,
    separator: str,
    duration_decimals: int,
) -> None:
    """Log endpoint success event."""
    logger.info(separator)
    logger.info(
        "✅ [SUCCESS] endpoint=%s | request_id=%s | ⏱️ duration_ms=%s",
        endpoint,
        request_id,
        _format_duration(duration_ms, duration_decimals),
    )
    logger.info(separator)


def log_endpoint_error(
    logger: logging.Logger,
    endpoint: str,
    request_id: str,
    duration_ms: Optional[float],
    separator: str,
    duration_decimals: int,
    exc: Optional[BaseException] = None,
) -> None:
    """Log endpoint error event with optional stack trace."""
    logger.error(separator)
    logger.error(
        "❌ [ERROR] endpoint=%s | request_id=%s | ⏱️ duration_ms=%s",
        endpoint,
        request_id,
        _format_duration(duration_ms, duration_decimals),
    )
    if exc is not None:
        logger.error("🔍 [TRACE] error=%s", exc, exc_info=True)
    logger.error(separator)


def build_log_separator(length: int) -> str:
    """Return a log separator string of the given length."""
    return "=" * max(length, MIN_SEPARATOR_LENGTH)


def _format_duration(duration_ms: Optional[float], decimals: int) -> str:
    """Return formatted duration string with the given precision."""
    if duration_ms is None:
        return "N/A"
    return f"{duration_ms:.{max(decimals, MIN_DECIMALS)}f}"
