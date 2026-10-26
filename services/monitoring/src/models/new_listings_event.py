from dataclasses import dataclass

from .listing import Listing
from .monitored_subscription import MonitoredVehicle


@dataclass(frozen=True, slots=True)
class NewListingsEvent:
    """Event published once per subscription when a run finds new listings."""

    event_id: str
    subscription_id: str
    email: str
    management_token: str
    vehicle: MonitoredVehicle
    state: str
    city: str
    radius_km: float
    listings: tuple[Listing, ...]
