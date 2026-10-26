"""Manage context variables included in structured log entries."""

from typing import Any
from uuid import uuid4

import structlog


def get_or_create_correlation_id(correlation_id: str | None = None) -> str:
    """Return a valid correlation ID or create one for the current flow."""
    if isinstance(correlation_id, str) and correlation_id.strip():
        return correlation_id.strip()

    return str(uuid4())


def get_correlation_id() -> str | None:
    """Return the correlation ID bound to the current execution context."""
    value = structlog.contextvars.get_contextvars().get("correlation_id")
    return value if isinstance(value, str) else None


def bind_context(**values: Any) -> None:
    """Bind values to the current logging context."""
    structlog.contextvars.bind_contextvars(**values)


def clear_context() -> None:
    """Clear context values bound to the current execution context."""
    structlog.contextvars.clear_contextvars()
