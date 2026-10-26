"""Configure structured JSON logging for a service."""

import logging

import structlog


def configure_logging(service_name: str) -> structlog.BoundLogger:
    """Configure structlog processors and return a logger bound to the service."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger().bind(service=service_name)
