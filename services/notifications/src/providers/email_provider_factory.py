import os

from ..config import get_brevo_api_key, get_mailjet_credentials
from ..ports.email_provider import EmailProvider
from .brevo.brevo_email_provider import BrevoEmailProvider
from .mailjet.mailjet_email_provider import MailjetEmailProvider


def build_email_provider() -> EmailProvider:
    """Build the configured email provider for the notifications runtime."""
    provider_name = os.environ.get("EMAIL_PROVIDER", "brevo").strip().lower()

    if provider_name == "brevo":
        return BrevoEmailProvider(
            api_key=get_brevo_api_key(),
            confirmation_template_id=int(os.environ["BREVO_CONFIRMATION_TEMPLATE_ID"]),
            new_listings_template_id=int(os.environ["BREVO_NEW_LISTINGS_TEMPLATE_ID"]),
            public_frontend_base_url=os.environ["PUBLIC_FRONTEND_BASE_URL"],
        )

    if provider_name == "mailjet":
        api_key, secret_key = get_mailjet_credentials()
        return MailjetEmailProvider(
            api_key=api_key,
            secret_key=secret_key,
            confirmation_template_id=int(os.environ["MAILJET_CONFIRMATION_TEMPLATE_ID"]),
            new_listings_template_id=int(os.environ["MAILJET_NEW_LISTINGS_TEMPLATE_ID"]),
            public_frontend_base_url=os.environ["PUBLIC_FRONTEND_BASE_URL"],
            sender_email=os.environ["MAILJET_SENDER_EMAIL"],
            sender_name=os.environ.get("MAILJET_SENDER_NAME"),
        )

    raise ValueError(f"Unsupported email provider: {provider_name}")
