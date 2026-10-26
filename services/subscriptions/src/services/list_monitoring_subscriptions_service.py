from ..models.monitoring_subscription import MonitoringSubscription
from ..ports.subscription_repository import SubscriptionRepository


class ListMonitoringSubscriptionsService:
    def __init__(self, repository: SubscriptionRepository) -> None:
        self._repository = repository

    def list_monitoring_subscriptions(self) -> list[MonitoringSubscription]:
        return [
            MonitoringSubscription(
                subscription_id=item.subscription_id, email=item.email,
                management_token=item.management_token, make_id=item.make_id,
                model_id=item.model_id, version_id=item.version_id, year_id=item.year_id,
                state=item.state, city=item.city, latitude=item.latitude,
                longitude=item.longitude, radius_km=item.radius_km,
                vehicle=item.vehicle, seen_listing_ids=item.seen_listing_ids,
            )
            for item in self._repository.list_active() if item.vehicle is not None
        ]
