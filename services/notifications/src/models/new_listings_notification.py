from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListingEmailItem:
    listing_id: str
    title: str
    price: float
    manufacture_year: str
    model_year: str
    odometer: int | None
    transmission: str | None
    seller_city: str | None
    seller_state: str | None
    seller_type: str | None
    listing_url: str | None = None


@dataclass(frozen=True, slots=True)
class NewListingsNotification:
    event_id: str
    subscription_id: str
    email: str
    management_token: str
    vehicle_name: str
    location: str
    listings: tuple[ListingEmailItem, ...]
