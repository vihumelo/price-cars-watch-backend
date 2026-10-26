from dataclasses import dataclass

from .subscription import SubscriptionVehicle


@dataclass(frozen=True, slots=True)
class MonitoringSubscription:
    """Hold active subscription data required by the monitoring job."""

    subscription_id: str
    email: str
    management_token: str
    make_id: str
    model_id: str
    version_id: str
    year_id: str
    state: str
    city: str
    latitude: float
    longitude: float
    radius_km: float
    vehicle: SubscriptionVehicle
    seen_listing_ids: tuple[str, ...]
