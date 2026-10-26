import json
import os
from typing import Any

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from services.shared.observability import configure_logging, get_correlation_id
from ..errors import VehicleListingsNotFoundError, VehicleListingsServiceUnavailableError
from ..models.listing_snapshot import ListingSnapshot
from ..ports.vehicle_listings_lookup import VehicleListingsLookup


logger = configure_logging("subscriptions")


class VehiclesApiListingsLookup(VehicleListingsLookup):
    """Read the internal Vehicles listing endpoint to establish a baseline."""

    DEFAULT_TIMEOUT = 15.0

    def __init__(
        self, http_client: httpx.Client | None = None, base_url: str | None = None,
        timeout: float | None = None, sign_requests: bool = True,
    ) -> None:
        self._http_client = http_client or httpx.Client(timeout=timeout or self.DEFAULT_TIMEOUT)
        self._base_url = (base_url or os.environ["VEHICLES_SERVICE_BASE_URL"]).rstrip("/")
        self._sign_requests = sign_requests

    def list_listings(
        self, make_id: str, model_id: str, version_id: str, year_id: str,
        state: str, city: str, latitude: float, longitude: float, radius_km: float,
    ) -> list[ListingSnapshot]:
        payload = {
            "makeId": make_id, "modelId": model_id, "versionId": version_id,
            "yearId": year_id, "state": state, "city": city,
            "latitude": latitude, "longitude": longitude, "radiusKm": radius_km,
        }
        url = f"{self._base_url}/internal/vehicles/listings"
        headers = {"content-type": "application/json"}
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["x-correlation-id"] = correlation_id
        body = json.dumps(payload)
        if self._sign_requests:
            headers = self._signed_headers(url, body, headers)
        try:
            response = self._http_client.post(url, content=body, headers=headers)
        except httpx.RequestError as exc:
            logger.exception(
                "vehicle_listings_request_failed",
                operation="list_listings",
                provider="vehicles_api",
                failure_type="request_error",
                path="/internal/vehicles/listings",
            )
            raise VehicleListingsServiceUnavailableError(
                "Vehicles service request failed",
            ) from exc
        provider_request_id = response.headers.get("x-amzn-requestid")
        if response.status_code == 404:
            logger.warning(
                "vehicle_listings_not_found",
                operation="list_listings",
                provider="vehicles_api",
                status_code=response.status_code,
                provider_request_id=provider_request_id,
                path="/internal/vehicles/listings",
            )
            raise VehicleListingsNotFoundError("Vehicle listings not found")
        try:
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise TypeError("Listings response must be an array")
            return [ListingSnapshot(listing_id=str(item["id"])) for item in data]
        except (httpx.HTTPStatusError, KeyError, TypeError, ValueError) as exc:
            logger.error(
                "vehicle_listings_request_failed",
                operation="list_listings",
                provider="vehicles_api",
                failure_type="http_response_error" if isinstance(exc, httpx.HTTPStatusError) else "invalid_response",
                status_code=response.status_code,
                provider_request_id=provider_request_id,
                path="/internal/vehicles/listings",
                response_body=response.text[:500],
            )
            raise VehicleListingsServiceUnavailableError(
                "Invalid Vehicles service response",
                status_code=response.status_code,
                provider_request_id=provider_request_id,
            ) from exc

    @staticmethod
    def _signed_headers(url: str, body: str, headers: dict[str, str]) -> dict[str, str]:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            raise VehicleListingsServiceUnavailableError("AWS credentials are unavailable")
        request = AWSRequest(method="POST", url=url, data=body, headers=headers)
        SigV4Auth(
            credentials.get_frozen_credentials(), "execute-api",
            os.getenv("AWS_REGION", session.region_name or "sa-east-1"),
        ).add_auth(request)
        return {str(key): str(value) for key, value in request.headers.items()}
