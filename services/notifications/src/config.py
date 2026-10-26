import json
import os
from typing import cast

from aws_lambda_powertools.utilities.parameters import get_secret


def get_brevo_api_key() -> str:
    """Read the cached Brevo key from AWS Secrets Manager."""
    return cast(str, get_secret(os.environ["BREVO_SECRET_NAME"], max_age=300))


def get_mailjet_credentials() -> tuple[str, str]:
    """Read the Mailjet API key and secret from AWS Secrets Manager."""
    secret = cast(str, get_secret(os.environ["MAILJET_SECRET_NAME"], max_age=300))
    try:
        values = json.loads(secret)
    except json.JSONDecodeError as exc:
        raise ValueError("Mailjet secret must contain a JSON object") from exc

    if not isinstance(values, dict):
        raise ValueError("Mailjet secret must contain a JSON object")
    api_key = values.get("MAILJET_API_KEY")
    secret_key = values.get("MAILJET_SECRET_KEY")
    if not isinstance(api_key, str) or not api_key:
        raise ValueError("Mailjet API key is missing")
    if not isinstance(secret_key, str) or not secret_key:
        raise ValueError("Mailjet secret key is missing")
    return api_key, secret_key
