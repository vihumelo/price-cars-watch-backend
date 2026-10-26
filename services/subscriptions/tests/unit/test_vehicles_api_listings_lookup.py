import httpx

from services.subscriptions.src.errors import VehicleListingsServiceUnavailableError
from services.subscriptions.src.providers.vehicles_api_listings_lookup import VehiclesApiListingsLookup


def test_list_listings_preserves_provider_error_context():
    def request(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            headers={"x-amzn-requestid": "api-request-123"},
            json={"message": "Forbidden"},
        )

    lookup = VehiclesApiListingsLookup(
        http_client=httpx.Client(transport=httpx.MockTransport(request)),
        base_url="https://vehicles.test",
        sign_requests=False,
    )

    try:
        lookup.list_listings("FIAT", "PULSE", "DRIVE", "2023", "São Paulo", "Santo André", -23.6, -46.5, 50)
    except VehicleListingsServiceUnavailableError as exc:
        assert exc.status_code == 403
        assert exc.provider_request_id == "api-request-123"
    else:
        raise AssertionError("Expected Vehicles service error")


def test_list_listings_wraps_request_error():
    def request(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed")

    lookup = VehiclesApiListingsLookup(
        http_client=httpx.Client(transport=httpx.MockTransport(request)),
        base_url="https://vehicles.test",
        sign_requests=False,
    )

    try:
        lookup.list_listings("FIAT", "PULSE", "DRIVE", "2023", "São Paulo", "Santo André", -23.6, -46.5, 50)
    except VehicleListingsServiceUnavailableError as exc:
        assert exc.status_code is None
        assert exc.provider_request_id is None
    else:
        raise AssertionError("Expected Vehicles service error")
