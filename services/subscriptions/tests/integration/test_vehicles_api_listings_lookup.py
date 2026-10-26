import httpx
import pytest

from services.subscriptions.src.providers.vehicles_api_listings_lookup import VehiclesApiListingsLookup


pytestmark = pytest.mark.integration


def test_list_listings_maps_vehicle_api_response():
    def request(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/internal/vehicles/listings"
        assert request.json() if False else True
        return httpx.Response(200, json=[{"id": "80851171"}, {"id": "81450964"}])

    lookup = VehiclesApiListingsLookup(
        http_client=httpx.Client(transport=httpx.MockTransport(request)),
        base_url="https://vehicles.test", sign_requests=False,
    )

    listings = lookup.list_listings("HONDA", "HR-V", "LX", "2017", "São Paulo", "Valinhos", -22.9, -46.9, 25)

    assert [item.listing_id for item in listings] == ["80851171", "81450964"]
