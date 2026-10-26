import json
from typing import Any


def event_body_from_record(record: dict[str, Any]) -> dict[str, Any]:
    """Decode either raw SNS delivery or the normal SNS-to-SQS envelope."""
    outer = json.loads(str(record["body"]))
    if not isinstance(outer, dict):
        raise ValueError("Queue message must be an object")
    message = outer.get("Message")
    if isinstance(message, str):
        inner = json.loads(message)
        if isinstance(inner, dict):
            return inner
        raise ValueError("SNS message must be an object")
    return outer


def correlation_id_from_record(record: dict[str, Any]) -> str | None:
    try:
        value = event_body_from_record(record).get("correlationId")
    except (KeyError, TypeError, ValueError):
        return None
    return value if isinstance(value, str) else None


def receive_attempt(record: dict[str, Any]) -> int | None:
    attributes = record.get("attributes")
    value = attributes.get("ApproximateReceiveCount") if isinstance(attributes, dict) else None
    try:
        return int(value) if isinstance(value, str) else None
    except ValueError:
        return None
