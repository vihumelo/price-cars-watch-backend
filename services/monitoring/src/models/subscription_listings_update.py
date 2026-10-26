from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SubscriptionListingsUpdate:
    subscription_id: str
    seen_listing_ids: tuple[str, ...]
    last_checked_at: datetime
