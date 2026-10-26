from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from services.shared.observability import configure_logging
from ..models.monitored_subscription import MonitoredSubscription
from ..models.new_listings_event import NewListingsEvent
from ..models.subscription_listings_update import SubscriptionListingsUpdate
from ..ports.monitored_subscription_reader import MonitoredSubscriptionReader
from ..ports.new_listings_publisher import NewListingsPublisher
from ..ports.subscription_listings_updater import SubscriptionListingsUpdater
from ..ports.vehicle_listings_lookup import VehicleListingsLookup

logger = configure_logging("monitoring")


class MonitoringService:
    """Compare current listings with each subscription baseline and notify new IDs."""

    def __init__(self, subscription_reader: MonitoredSubscriptionReader,
                 subscription_listings_updater: SubscriptionListingsUpdater,
                 vehicle_listings_lookup: VehicleListingsLookup,
                 new_listings_publisher: NewListingsPublisher) -> None:
        self._subscription_reader = subscription_reader
        self._subscription_listings_updater = subscription_listings_updater
        self._vehicle_listings_lookup = vehicle_listings_lookup
        self._new_listings_publisher = new_listings_publisher

    def run(self, run_id: str, checked_at: datetime | None = None) -> dict[str, int]:
        checked_at = checked_at or datetime.now(UTC)
        groups = self._subscriptions_by_criteria(self._subscription_reader.list_active_subscriptions())
        subscriptions_checked = 0
        new_listings_detected = 0
        notifications_published = 0

        for subscriptions in groups.values():
            reference = subscriptions[0]
            current_listings = self._unique_listings(self._vehicle_listings_lookup.list_listings(
                reference.make_id, reference.model_id, reference.version_id, reference.year_id,
                reference.state, reference.city, reference.latitude, reference.longitude,
                reference.radius_km,
            ))
            current_ids = tuple(listing.listing_id for listing in current_listings)
            for subscription in subscriptions:
                subscriptions_checked += 1
                known_ids = set(subscription.seen_listing_ids)
                new_listings = tuple(listing for listing in current_listings if listing.listing_id not in known_ids)
                next_seen_ids = tuple(dict.fromkeys((*subscription.seen_listing_ids, *current_ids)))
                updated = self._subscription_listings_updater.update_listings(
                    SubscriptionListingsUpdate(subscription.subscription_id, next_seen_ids, checked_at)
                )
                if not updated or not new_listings:
                    continue
                self._new_listings_publisher.publish(NewListingsEvent(
                    event_id=self._event_id(run_id, subscription, new_listings),
                    subscription_id=subscription.subscription_id, email=subscription.email,
                    management_token=subscription.management_token, vehicle=subscription.vehicle,
                    state=subscription.state, city=subscription.city, radius_km=subscription.radius_km,
                    listings=new_listings,
                ))
                new_listings_detected += len(new_listings)
                notifications_published += 1
                logger.info("new_listings_detected", run_id=run_id,
                            subscription_id=subscription.subscription_id, count=len(new_listings))

        return {
            "subscriptions_checked": subscriptions_checked,
            "listing_searches": len(groups),
            "new_listings_detected": new_listings_detected,
            "notifications_published": notifications_published,
        }

    @staticmethod
    def _subscriptions_by_criteria(subscriptions: list[MonitoredSubscription]) -> dict[tuple[object, ...], list[MonitoredSubscription]]:
        groups: dict[tuple[object, ...], list[MonitoredSubscription]] = {}
        for item in subscriptions:
            key = (item.make_id, item.model_id, item.version_id, item.year_id, item.state,
                   item.city, item.latitude, item.longitude, item.radius_km)
            groups.setdefault(key, []).append(item)
        return groups

    @staticmethod
    def _unique_listings(listings):
        by_id = {}
        for listing in listings:
            by_id.setdefault(listing.listing_id, listing)
        return tuple(by_id.values())

    @staticmethod
    def _event_id(run_id: str, subscription: MonitoredSubscription, listings) -> str:
        ids = ":".join(listing.listing_id for listing in listings)
        return str(uuid5(NAMESPACE_URL, f"{run_id}:{subscription.subscription_id}:{ids}"))
