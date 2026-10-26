from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonitoredVehicle:
    make: str
    model: str
    version: str
    year: str


@dataclass(frozen=True, slots=True)
class MonitoredSubscription:
    """Active subscription data used by one monitoring pass."""

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
    vehicle: MonitoredVehicle
    seen_listing_ids: tuple[str, ...]
