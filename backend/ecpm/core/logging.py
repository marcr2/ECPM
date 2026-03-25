"""Structured logging configuration using structlog."""

import logging
import re
import sys

import structlog

from ecpm.config import get_settings

_SENSITIVE_PATTERNS = [
    (re.compile(r"(password|passwd|pwd)\s*[=:]\s*\S+", re.IGNORECASE), r"\1=***REDACTED***"),
    (re.compile(r"(api[_-]?key|secret[_-]?key|token)\s*[=:]\s*\S+", re.IGNORECASE), r"\1=***REDACTED***"),
    (re.compile(r"(Bearer\s+)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"postgresql(\+\w+)?://[^@]+@"), "postgresql\\1://***:***@"),
    (re.compile(r"redis://:[^@]+@"), "redis://:***@"),
]


def _redact_sensitive_data(
    _logger: logging.Logger, _method: str, event_dict: dict
) -> dict:
    """Structlog processor that redacts passwords, keys, and tokens from log output."""
    for key, value in list(event_dict.items()):
        if not isinstance(value, str):
            continue
        for pattern, replacement in _SENSITIVE_PATTERNS:
            value = pattern.sub(replacement, value)
        event_dict[key] = value
    return event_dict


def setup_logging() -> None:
    """Configure structlog with JSON renderer for production, console for dev.

    Production (log_level != DEBUG): JSON lines, machine-parseable.
    Development (log_level == DEBUG): Colored console output, human-readable.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _redact_sensitive_data,
    ]

    if settings.log_level.upper() == "DEBUG":
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
