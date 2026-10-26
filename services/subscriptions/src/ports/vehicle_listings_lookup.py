from typing import Protocol

from ..models.listing_snapshot import ListingSnapshot


class VehicleListingsLookup(Protocol):
    def list_listings(
        self, make_id: str, model_id: str, version_id: str, year_id: str,
        state: str, city: str, latitude: float, longitude: float, radius_km: float,
    ) -> list[ListingSnapshot]: ...
