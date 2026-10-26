from dataclasses import replace

from ..models.subscription import SubscriptionStatus
from ..models.subscription_listings_update import SubscriptionListingsUpdate
from ..ports.subscription_repository import SubscriptionRepository


class UpdateSubscriptionListingsService:
    """Persist a monitor's seen-listing set only while subscription is active."""

    def __init__(self, repository: SubscriptionRepository) -> None:
        self._repository = repository

    def update_subscription_listings(self, update: SubscriptionListingsUpdate) -> bool:
        subscription = self._repository.get_by_id(update.subscription_id)
        if subscription is None or subscription.status != SubscriptionStatus.ACTIVE:
            return False
        self._repository.update(replace(
            subscription,
            seen_listing_ids=tuple(dict.fromkeys(update.seen_listing_ids)),
            last_checked_at=update.last_checked_at,
        ))
        return True
