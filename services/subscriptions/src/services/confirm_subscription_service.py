from dataclasses import replace
from datetime import UTC, datetime

from ..errors import InvalidConfirmationLinkError
from ..models.subscription import SubscriptionStatus, SubscriptionVehicle
from ..ports.subscription_repository import SubscriptionRepository
from ..ports.vehicle_listings_lookup import VehicleListingsLookup


class ConfirmSubscriptionService:
    """Capture existing listings as baseline before activating a subscription."""

    def __init__(self, repository: SubscriptionRepository, listings_lookup: VehicleListingsLookup) -> None:
        self._repository = repository
        self._listings_lookup = listings_lookup

    def confirm_subscription(self, subscription_id: str, token: str) -> None:
        subscription = self._repository.get_by_id(subscription_id)
        if (subscription is None or subscription.status != SubscriptionStatus.PENDING_CONFIRMATION
                or token != subscription.confirmation_token):
            raise InvalidConfirmationLinkError("Invalid confirmation link")
        listings = self._listings_lookup.list_listings(
            subscription.make_id, subscription.model_id, subscription.version_id, subscription.year_id,
            subscription.state, subscription.city, subscription.latitude, subscription.longitude,
            subscription.radius_km,
        )
        seen_listing_ids = tuple(dict.fromkeys(item.listing_id for item in listings))
        now = datetime.now(UTC)
        vehicle = SubscriptionVehicle(subscription.make_id, subscription.model_id,
                                      subscription.version_id, subscription.year_id)
        confirmed = replace(
            subscription, status=SubscriptionStatus.ACTIVE, confirmation_token=None, vehicle=vehicle,
            seen_listing_ids=seen_listing_ids, confirmed_at=now, last_checked_at=now,
            baseline_captured_at=now,
        )
        self._repository.update(confirmed)
