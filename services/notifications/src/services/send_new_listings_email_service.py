from ..models.new_listings_notification import NewListingsNotification
from ..ports.email_provider import EmailProvider


class SendNewListingsEmailService:
    """Send one notification containing every newly found listing."""

    def __init__(self, email_provider: EmailProvider) -> None:
        self._email_provider = email_provider

    def send_new_listings_email(self, notification: NewListingsNotification) -> None:
        self._email_provider.send_new_listings(notification)
