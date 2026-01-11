"""Structured logging configuration for Marvel metadata.

Supports both JSON and text output formats.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Literal


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production use."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add common context fields
        if hasattr(record, "year"):
            log_data["year"] = record.year
        if hasattr(record, "issue_count"):
            log_data["issue_count"] = record.issue_count

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(
    level: str = "INFO",
    format: Literal["json", "text"] = "text",
) -> None:
    """Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" for production, "text" for development)

    Example:
        >>> setup_logging(level="DEBUG", format="text")
        >>> logger = get_logger("my_module")
        >>> logger.info("Application started")
    """
    root_logger = logging.getLogger("marvel_metadata")
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Prevent propagation to root logger
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name (will be prefixed with "marvel_metadata.")

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger("decoder")
        >>> logger.info("Decoding payload", extra={"year": 2022})
    """
    return logging.getLogger(f"marvel_metadata.{name}")


class LogContext:
    """Context manager for adding extra fields to log records."""

    def __init__(self, logger: logging.Logger, **fields: Any) -> None:
        self.logger = logger
        self.fields = fields
        self._old_factory: Any = None

    def __enter__(self) -> logging.Logger:
        self._old_factory = logging.getLogRecordFactory()

        def record_factory(
            *args: Any, **kwargs: Any
        ) -> logging.LogRecord:
            record = self._old_factory(*args, **kwargs)
            for key, value in self.fields.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self.logger

    def __exit__(self, *args: Any) -> None:
        logging.setLogRecordFactory(self._old_factory)
