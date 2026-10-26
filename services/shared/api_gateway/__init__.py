"""Helpers for reading API Gateway events and request data."""

import base64
import json
from typing import Any


def route_key(event: dict[str, Any]) -> str | None:
    """Return the route key from either supported API Gateway event location."""
    value = event.get("routeKey")
    if value is not None:
        return str(value)

    request_context = event.get("requestContext") or {}
    value = request_context.get("routeKey")
    if value is not None:
        return str(value)

    return None


def path_parameter(event: dict[str, Any], name: str) -> str | None:
    """Return a non-empty string path parameter, or None if it is missing."""
    path_parameters = event.get("pathParameters") or {}
    value = path_parameters.get(name)
    if not is_non_empty_string(value):
        return None

    return str(value)


def query_parameter(event: dict[str, Any], name: str) -> str | None:
    """Return a non-empty string query parameter, or None if it is missing."""
    query_parameters = event.get("queryStringParameters") or {}
    value = query_parameters.get(name)
    if not is_non_empty_string(value):
        return None

    return str(value)


def json_body(event: dict[str, Any]) -> Any | None:
    """Decode and parse an event body, returning None when it is invalid."""
    body = event.get("body")
    if body is None:
        return None

    if event.get("isBase64Encoded") is True:
        try:
            body = base64.b64decode(body).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    try:
        return json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return None


def is_non_empty_string(value: Any) -> bool:
    """Check that a value is a string containing non-whitespace characters."""
    return isinstance(value, str) and value.strip() != ""


__all__ = [
    "is_non_empty_string",
    "json_body",
    "path_parameter",
    "query_parameter",
    "route_key",
]
