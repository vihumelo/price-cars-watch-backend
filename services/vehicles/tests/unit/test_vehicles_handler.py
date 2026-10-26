import json
from unittest.mock import Mock

import pytest

from services.vehicles.src.errors import VehicleNotFoundError, VehicleProviderUnavailableError
from services.vehicles.src.handlers import vehicles
from services.vehicles.src.models.vehicle import VehicleSelection


pytestmark = pytest.mark.filterwarnings("ignore:No application metrics to publish.*:UserWarning")


@pytest.fixture
def context() -> Mock:
    return Mock(aws_request_id="request-123")


def test_handler_dispatches_make_route_and_serializes_response(monkeypatch, context, sample_make):
    service = Mock()
    service.list_makes.return_value = [sample_make]
    monkeypatch.setattr(vehicles, "service", service)

    response = vehicles.handler({"routeKey": "GET /vehicles/makes"}, context)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == [{"id": "HONDA", "name": "HONDA"}]
    service.list_makes.assert_called_once_with()


def test_handler_dispatches_vehicle_selection_route(monkeypatch, context):
    service = Mock()
    service.get_vehicle.return_value = VehicleSelection("FIAT", "PULSE", "DRIVE", "2023")
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years/{yearId}",
        "pathParameters": {
            "makeId": "FIAT",
            "modelId": "PULSE",
            "versionId": "DRIVE",
            "yearId": "2023",
        },
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "make": "FIAT",
        "model": "PULSE",
        "version": "DRIVE",
        "year": "2023",
    }
    service.get_vehicle.assert_called_once_with("FIAT", "PULSE", "DRIVE", "2023")


def test_handler_dispatches_years_route(monkeypatch, context, sample_year):
    service = Mock()
    service.list_years.return_value = [sample_year]
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years",
        "pathParameters": {"makeId": "HONDA", "modelId": "CIVIC", "versionId": "TOURING"},
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == [{"id": "2020", "name": "2020"}]
    service.list_years.assert_called_once_with("HONDA", "CIVIC", "TOURING")


def test_list_versions_returns_bad_request_when_model_is_missing(monkeypatch, context):
    service = Mock()
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "GET /vehicles/makes/{makeId}/models/{modelId}/versions",
        "pathParameters": {"makeId": "HONDA"},
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "INVALID_REQUEST"
    service.list_versions.assert_not_called()


def test_list_listings_serializes_normalized_internal_response(
    monkeypatch, context, sample_listing
):
    service = Mock()
    service.list_listings.return_value = [sample_listing]
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "POST /internal/vehicles/listings",
        "body": json.dumps(
            {
                "makeId": "VOLKSWAGEN",
                "modelId": "GOLF",
                "versionId": "SPORTLINE",
                "yearId": "2009",
                "state": "São Paulo",
                "city": "Santo André",
                "latitude": -23.66389,
                "longitude": -46.53833,
                "radiusKm": 25,
            }
        ),
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == 200
    assert json.loads(response["body"])[0] == {
        "id": "80947084",
        "provider": "webmotors",
        "providerListingId": "80947084",
        "title": "VOLKSWAGEN GOLF 1.6 MI SPORTLINE 8V FLEX 4P MANUAL",
        "make": "VOLKSWAGEN",
        "model": "GOLF",
        "version": "1.6 MI SPORTLINE 8V FLEX 4P MANUAL",
        "manufactureYear": "2008",
        "modelYear": "2009",
        "price": 42000,
        "odometer": 177767,
        "transmission": "Manual",
        "auction": False,
        "armored": "N",
        "sellerCity": "Jacarezinho",
        "sellerState": "Paraná (PR)",
        "sellerType": "PJ",
        "listingUrl": "https://www.webmotors.com.br/comprar/volkswagen/golf/16-mi-sportline-8v-flex-4p-manual/4-portas/2008-2009/80947084",
    }
    service.list_listings.assert_called_once()
    location = service.list_listings.call_args.args[4]
    assert location.city == "Santo André"
    assert location.radius_km == 25.0


def test_list_listings_accepts_zero_radius(monkeypatch, context):
    service = Mock()
    service.list_listings.return_value = []
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "POST /internal/vehicles/listings",
        "body": json.dumps({
            "makeId": "HONDA",
            "modelId": "HR-V",
            "versionId": "LX",
            "yearId": "2017",
            "state": "São Paulo",
            "city": "Santo André",
            "latitude": -23.66389,
            "longitude": -46.53833,
            "radiusKm": 0,
        }),
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == 200
    assert service.list_listings.call_args.args[4].radius_km == 0.0


def test_list_listings_rejects_partial_coordinates(monkeypatch, context):
    service = Mock()
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "POST /internal/vehicles/listings",
        "body": json.dumps(
            {
                "makeId": "HONDA",
                "modelId": "HR-V",
                "versionId": "LX",
                "yearId": "2017",
                "latitude": -23.66389,
            }
        ),
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == 400
    service.list_listings.assert_not_called()


@pytest.mark.parametrize(
    ("exception", "status_code", "code"),
    [
        (VehicleNotFoundError(), 404, "VEHICLE_NOT_FOUND"),
        (VehicleProviderUnavailableError("provider unavailable"), 502, "VEHICLE_PROVIDER_UNAVAILABLE"),
    ],
)
def test_list_years_maps_domain_errors(monkeypatch, context, exception, status_code, code):
    service = Mock()
    service.list_years.side_effect = exception
    monkeypatch.setattr(vehicles, "service", service)
    event = {
        "routeKey": "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years",
        "pathParameters": {"makeId": "HONDA", "modelId": "CIVIC", "versionId": "TOURING"},
    }

    response = vehicles.handler(event, context)

    assert response["statusCode"] == status_code
    assert json.loads(response["body"])["code"] == code
