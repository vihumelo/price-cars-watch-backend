from typing import Protocol

from ..models.subscription_confirmation_event import SubscriptionConfirmationEvent


class ConfirmationEmailPublisher(Protocol):
    def publish(self, event: SubscriptionConfirmationEvent) -> None: ...
