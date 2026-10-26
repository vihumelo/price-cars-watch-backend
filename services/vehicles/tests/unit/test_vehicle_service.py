from services.vehicles.src.models.vehicle import ListingLocation, VehicleSelection
from services.vehicles.src.services.vehicle_service import VehicleService


def test_list_makes_delegates_to_provider(vehicle_provider, sample_make):
    vehicle_provider.list_makes.return_value = [sample_make]
    service = VehicleService(vehicle_provider)

    assert service.list_makes() == [sample_make]
    vehicle_provider.list_makes.assert_called_once_with()


def test_get_vehicle_delegates_all_identifiers(vehicle_provider):
    vehicle = VehicleSelection("HONDA", "CIVIC", "TOURING", "2020")
    vehicle_provider.get_vehicle.return_value = vehicle
    service = VehicleService(vehicle_provider)

    assert service.get_vehicle("HONDA", "CIVIC", "TOURING", "2020") == vehicle
    vehicle_provider.get_vehicle.assert_called_once_with(
        "HONDA", "CIVIC", "TOURING", "2020"
    )


def test_list_years_delegates_all_identifiers(vehicle_provider, sample_year):
    vehicle_provider.list_years.return_value = [sample_year]
    service = VehicleService(vehicle_provider)

    assert service.list_years("HONDA", "CIVIC", "TOURING") == [sample_year]
    vehicle_provider.list_years.assert_called_once_with("HONDA", "CIVIC", "TOURING")


def test_list_listings_delegates_location(vehicle_provider, sample_listing):
    location = ListingLocation(
        city="Santo André",
        state="São Paulo",
        latitude=-23.66389,
        longitude=-46.53833,
        radius_km=25.0,
    )
    vehicle_provider.list_listings.return_value = [sample_listing]
    service = VehicleService(vehicle_provider)

    assert service.list_listings("VOLKSWAGEN", "GOLF", "SPORTLINE", "2009", location) == [
        sample_listing
    ]
    vehicle_provider.list_listings.assert_called_once_with(
        "VOLKSWAGEN", "GOLF", "SPORTLINE", "2009", location
    )
