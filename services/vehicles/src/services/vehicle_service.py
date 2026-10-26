from ..models.vehicle import (
    Listing,
    ListingLocation,
    Make,
    VehicleModel,
    VehicleSelection,
    VehicleVersion,
    VehicleYear,
)
from ..ports.vehicle_provider import VehicleProvider


class VehicleService:
    """Expose vehicle operations to handlers independently of the provider."""

    def __init__(self, vehicle_provider: VehicleProvider) -> None:
        self._vehicle_provider = vehicle_provider

    def list_makes(self) -> list[Make]:
        return self._vehicle_provider.list_makes()

    def list_models(self, make_id: str) -> list[VehicleModel]:
        return self._vehicle_provider.list_models(make_id)

    def list_versions(self, make_id: str, model_id: str) -> list[VehicleVersion]:
        return self._vehicle_provider.list_versions(make_id, model_id)

    def list_years(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
    ) -> list[VehicleYear]:
        return self._vehicle_provider.list_years(make_id, model_id, version_id)

    def get_vehicle(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
        year_id: str,
    ) -> VehicleSelection:
        return self._vehicle_provider.get_vehicle(
            make_id,
            model_id,
            version_id,
            year_id,
        )

    def list_listings(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
        year_id: str,
        location: ListingLocation,
    ) -> list[Listing]:
        return self._vehicle_provider.list_listings(
            make_id,
            model_id,
            version_id,
            year_id,
            location,
        )
