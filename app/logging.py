"""Logging configuration for tana-connector.

Provides structured logging using structlog with configurable output format.
In debug mode, uses colored console output. In production, uses JSON format.

Usage:
    from app.logging import get_logger, setup_logging

    # Setup logging at app startup
    setup_logging(debug=True)

    # Get a logger in any module
    logger = get_logger(__name__)
    logger.info("Processing request", user_id=123, action="fetch_events")
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def setup_logging(debug: bool = False, log_level: str | None = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        debug: If True, uses colored console output. If False, uses JSON format.
        log_level: Override log level. If None, uses DEBUG for debug mode, INFO otherwise.
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = logging.DEBUG if debug else logging.INFO

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Suppress noisy third-party loggers
    noisy_loggers = [
        "httpx",
        "httpcore",
        "hpack",
        "azure",
        "msal",
        "urllib3",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Shared processors for all modes
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if debug:
        # Development: colored console output
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Module name, typically __name__

    Returns:
        Configured structlog logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Event created", event_id="123", subject="Meeting")
    """
    return structlog.get_logger(name)


def log_context(**kwargs: Any) -> structlog.contextvars.bound_contextvars:
    """
    Context manager to add context to all log messages within the block.

    Args:
        **kwargs: Key-value pairs to add to log context

    Returns:
        Context manager that binds the given context

    Example:
        with log_context(request_id="abc123", user="john@example.com"):
            logger.info("Processing request")  # Includes request_id and user
            do_something()
            logger.info("Request complete")  # Also includes request_id and user
    """
    return structlog.contextvars.bound_contextvars(**kwargs)
