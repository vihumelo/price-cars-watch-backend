from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Make:
    """A vehicle make returned by a vehicle data provider."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class VehicleModel:
    """A vehicle model associated with a make."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class VehicleVersion:
    """A complete vehicle version associated with a model."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class VehicleYear:
    """A model year available for a vehicle version."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class ListingLocation:
    """Optional geographic criteria used to search vehicle listings."""

    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = None


@dataclass(frozen=True, slots=True)
class VehicleSelection:
    """A complete vehicle resolved from make, model, version, and year."""

    make: str
    model: str
    version: str
    year: str


@dataclass(frozen=True, slots=True)
class Listing:
    """A normalized vehicle listing returned by a provider search."""

    id: str
    provider: str
    provider_listing_id: str
    title: str
    make: str
    model: str
    version: str
    manufacture_year: str
    model_year: str
    price: int | float
    odometer: int | None
    transmission: str | None
    auction: bool | None
    armored: str | None
    seller_city: str | None
    seller_state: str | None
    seller_type: str | None
    listing_url: str | None = None
