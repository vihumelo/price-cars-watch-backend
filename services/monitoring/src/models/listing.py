from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Listing:
    """Normalized Webmotors listing used for new-listing notifications."""

    listing_id: str
    title: str
    make: str
    model: str
    version: str
    manufacture_year: str
    model_year: str
    price: float
    odometer: int | None
    transmission: str | None
    auction: bool | None
    armored: str | None
    seller_city: str | None
    seller_state: str | None
    seller_type: str | None
    listing_url: str | None = None
