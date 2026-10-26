from dataclasses import replace
from datetime import UTC, datetime

from ..errors import SubscriptionAccessDeniedError
from ..models.subscription import SubscriptionStatus
from ..ports.subscription_repository import SubscriptionRepository


class CancelSubscriptionService:
    def __init__(self, repository: SubscriptionRepository) -> None:
        self._repository = repository

    def cancel_subscription(self, subscription_id: str, management_token: str) -> None:
        subscription = self._repository.get_by_id(subscription_id)
        if subscription is None or management_token != subscription.management_token:
            raise SubscriptionAccessDeniedError("Subscription access denied")
        if subscription.status != SubscriptionStatus.CANCELLED:
            self._repository.update(replace(subscription, status=SubscriptionStatus.CANCELLED,
                                            cancelled_at=datetime.now(UTC)))
