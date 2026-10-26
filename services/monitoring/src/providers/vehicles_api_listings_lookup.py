import json
import os
from typing import Any

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from services.shared.observability import get_correlation_id
from ..errors import VehiclesServiceUnavailableError
from ..models.listing import Listing
from ..ports.vehicle_listings_lookup import VehicleListingsLookup


class VehiclesApiListingsLookup(VehicleListingsLookup):
    """Read normalized current listings from the internal Vehicles endpoint."""

    DEFAULT_TIMEOUT = 20.0

    def __init__(self, http_client: httpx.Client | None = None, base_url: str | None = None,
                 region_name: str | None = None, session: Any | None = None,
                 timeout: float | None = None) -> None:
        self._http_client = http_client or httpx.Client(timeout=timeout or self.DEFAULT_TIMEOUT)
        self._base_url = (base_url or os.environ["VEHICLES_SERVICE_BASE_URL"]).rstrip("/")
        self._region_name = region_name or os.environ.get("AWS_REGION", "sa-east-1")
        self._session = session or boto3.Session()

    def list_listings(self, make_id: str, model_id: str, version_id: str, year_id: str,
                      state: str, city: str, latitude: float, longitude: float,
                      radius_km: float) -> list[Listing]:
        body = json.dumps({
            "makeId": make_id, "modelId": model_id, "versionId": version_id, "yearId": year_id,
            "state": state, "city": city, "latitude": latitude, "longitude": longitude,
            "radiusKm": radius_km,
        }, separators=(",", ":")).encode()
        response = self._request(body)
        try:
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Listings response must be an array")
            return [self._listing_from_dict(item) for item in payload]
        except (httpx.HTTPStatusError, KeyError, TypeError, ValueError) as exc:
            raise VehiclesServiceUnavailableError("Invalid Vehicles service response") from exc

    def _request(self, body: bytes) -> httpx.Response:
        url = f"{self._base_url}/internal/vehicles/listings"
        headers = {"Content-Type": "application/json"}
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["x-correlation-id"] = correlation_id
        request = AWSRequest(method="POST", url=url, data=body, headers=headers)
        credentials = self._session.get_credentials()
        if credentials is None:
            raise VehiclesServiceUnavailableError("AWS credentials are unavailable")
        SigV4Auth(credentials.get_frozen_credentials(), "execute-api", self._region_name).add_auth(request)
        try:
            return self._http_client.post(url, content=body, headers=dict(request.headers.items()))
        except httpx.RequestError as exc:
            raise VehiclesServiceUnavailableError("Vehicles service request failed") from exc

    @staticmethod
    def _listing_from_dict(data: Any) -> Listing:
        if not isinstance(data, dict):
            raise ValueError("Invalid listing")
        return Listing(
            listing_id=str(data["id"]), title=str(data["title"]), make=str(data["make"]),
            model=str(data["model"]), version=str(data["version"]),
            manufacture_year=str(data["manufactureYear"]), model_year=str(data["modelYear"]),
            price=float(data["price"]), odometer=_optional_int(data.get("odometer")),
            transmission=_optional_string(data.get("transmission")), auction=_optional_bool(data.get("auction")),
            armored=_optional_string(data.get("armored")), seller_city=_optional_string(data.get("sellerCity")),
            seller_state=_optional_string(data.get("sellerState")), seller_type=_optional_string(data.get("sellerType")),
            listing_url=_optional_string(data.get("listingUrl")),
        )


def _optional_string(value: Any) -> str | None:
    return str(value) if value is not None else None


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None and not isinstance(value, bool) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
