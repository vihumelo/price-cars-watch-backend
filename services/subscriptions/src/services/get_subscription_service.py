from ..errors import SubscriptionAccessDeniedError
from ..models.subscription import Subscription
from ..ports.subscription_repository import SubscriptionRepository


class GetSubscriptionService:
    def __init__(self, repository: SubscriptionRepository) -> None:
        self._repository = repository

    def get_subscription(self, subscription_id: str, management_token: str) -> Subscription:
        subscription = self._repository.get_by_id(subscription_id)
        if subscription is None or management_token != subscription.management_token:
            raise SubscriptionAccessDeniedError("Subscription access denied")
        return subscription
