from ..models.confirmation_email_request import ConfirmationEmailRequest
from ..ports.email_provider import EmailProvider


class SendConfirmationEmailService:
    """Keep the FIPE Watch confirmation e-mail contract unchanged."""

    def __init__(self, email_provider: EmailProvider) -> None:
        self._email_provider = email_provider

    def send_confirmation_email(self, request: ConfirmationEmailRequest) -> None:
        self._email_provider.send_confirmation(request)
