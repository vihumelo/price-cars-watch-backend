from typing import Protocol

from ..models.subscription_listings_update import SubscriptionListingsUpdate


class SubscriptionListingsUpdater(Protocol):
    def update_listings(self, update: SubscriptionListingsUpdate) -> bool: ...
