from typing import Protocol

from ..models.confirmation_email_request import ConfirmationEmailRequest
from ..models.new_listings_notification import NewListingsNotification


class EmailProvider(Protocol):
    def send_confirmation(self, request: ConfirmationEmailRequest) -> None: ...

    def send_new_listings(self, notification: NewListingsNotification) -> None: ...
