from typing import Protocol

from ..models.vehicle import (
    Listing,
    ListingLocation,
    Make,
    VehicleModel,
    VehicleSelection,
    VehicleVersion,
    VehicleYear,
)


class VehicleProvider(Protocol):
    def list_makes(self) -> list[Make]:
        """Return the vehicle makes available from the provider."""
        ...

    def list_models(self, make_id: str) -> list[VehicleModel]:
        """Return the models available for a make."""
        ...

    def list_versions(self, make_id: str, model_id: str) -> list[VehicleVersion]:
        """Return the versions available for a make and model."""
        ...

    def list_years(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
    ) -> list[VehicleYear]:
        """Return the model years available for a vehicle version."""
        ...

    def get_vehicle(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
        year_id: str,
    ) -> VehicleSelection:
        """Return the complete vehicle resolved from the selected identifiers."""
        ...

    def list_listings(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
        year_id: str,
        location: ListingLocation,
    ) -> list[Listing]:
        """Return listings matching an exact vehicle and location selection."""
        ...
