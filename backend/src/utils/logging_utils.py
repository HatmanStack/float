"""Structured logging utility for Lambda functions.

Provides JSON-formatted logging appropriate for CloudWatch,
with safeguards against logging sensitive data.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

# Sensitive field names that should be redacted
SENSITIVE_FIELDS = frozenset({
    "audio",
    "base64_audio",
    "base64",
    "password",
    "token",
    "api_key",
    "secret",
    "credential",
    "authorization",
})

# Maximum length for any logged value (prevents huge logs)
MAX_VALUE_LENGTH = 500


class SensitiveDataFilter(logging.Filter):
    """Filter that redacts sensitive data from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "data") and isinstance(record.data, dict):
            record.data = self._redact_sensitive(record.data)
        return True

    def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive fields from a dictionary."""
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            lower_key = key.lower()
            if any(sensitive in lower_key for sensitive in SENSITIVE_FIELDS):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self._redact_sensitive(value)
            elif isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
                result[key] = f"{value[:100]}...[truncated, {len(value)} chars total]"
            else:
                result[key] = value
        return result


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging in CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra data if present
        if hasattr(record, "data"):
            log_entry["data"] = record.data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add request context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for the given module name.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Set level from environment, default to INFO
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Create handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler.addFilter(SensitiveDataFilter())

        logger.addHandler(handler)
        logger.propagate = False

    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    exc_info: bool = False,
) -> None:
    """Log a message with optional context data.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO)
        message: Log message
        request_id: Optional request identifier
        user_id: Optional user identifier
        data: Optional dictionary of additional data
        exc_info: Whether to include exception info
    """
    extra = {}
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id
    if data:
        extra["data"] = data

    logger.log(level, message, extra=extra, exc_info=exc_info)
