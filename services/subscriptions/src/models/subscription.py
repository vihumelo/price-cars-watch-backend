from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SubscriptionStatus(StrEnum):
    """Represent the lifecycle states of a listings subscription."""

    PENDING_CONFIRMATION = "pending_confirmation"
    ACTIVE = "active"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class SubscriptionVehicle:
    """Store the exact provider-neutral vehicle selection."""

    make: str
    model: str
    version: str
    year: str


@dataclass(frozen=True, slots=True)
class Subscription:
    """Represent a subscription, its location criteria, and seen listing baseline."""

    subscription_id: str
    subscription_key: str
    email: str
    make_id: str
    model_id: str
    version_id: str
    year_id: str
    state: str
    city: str
    latitude: float
    longitude: float
    radius_km: float
    status: SubscriptionStatus
    management_token: str
    created_at: datetime
    confirmation_token: str | None = None
    vehicle: SubscriptionVehicle | None = None
    seen_listing_ids: tuple[str, ...] = ()
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    last_checked_at: datetime | None = None
    baseline_captured_at: datetime | None = None
