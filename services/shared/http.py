"""Build response dictionaries in the format expected by API Gateway."""

import json
from typing import Any


def json_response(status_code: int, body: Any) -> dict[str, Any]:
    """Serialize a response body as JSON and set its content type."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def error_response(status_code: int, code: str, message: str) -> dict[str, Any]:
    """Build a JSON error response with a stable code and message."""
    return json_response(status_code, {"code": code, "message": message})
