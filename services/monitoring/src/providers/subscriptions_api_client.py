import json
import os
from typing import Any

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from services.shared.observability import get_correlation_id
from ..errors import SubscriptionsServiceUnavailableError
from ..models.monitored_subscription import MonitoredSubscription, MonitoredVehicle
from ..models.subscription_listings_update import SubscriptionListingsUpdate
from ..ports.monitored_subscription_reader import MonitoredSubscriptionReader
from ..ports.subscription_listings_updater import SubscriptionListingsUpdater


class SubscriptionsApiClient(MonitoredSubscriptionReader, SubscriptionListingsUpdater):
    """Access internal subscriptions routes with AWS SigV4 authentication."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self, http_client: httpx.Client | None = None, base_url: str | None = None,
                 region_name: str | None = None, session: Any | None = None,
                 timeout: float | None = None) -> None:
        self._http_client = http_client or httpx.Client(timeout=timeout or self.DEFAULT_TIMEOUT)
        self._base_url = (base_url or os.environ["SUBSCRIPTIONS_SERVICE_BASE_URL"]).rstrip("/")
        self._region_name = region_name or os.environ.get("AWS_REGION", "sa-east-1")
        self._session = session or boto3.Session()

    def list_active_subscriptions(self) -> list[MonitoredSubscription]:
        response = self._request("GET", "/internal/subscriptions/monitoring")
        try:
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Monitoring response must be an array")
            return [self._from_dict(item) for item in payload]
        except (httpx.HTTPStatusError, TypeError, ValueError, KeyError) as exc:
            raise SubscriptionsServiceUnavailableError("Invalid Subscriptions service response") from exc

    def update_listings(self, update: SubscriptionListingsUpdate) -> bool:
        body = json.dumps({
            "seenListings": list(update.seen_listing_ids),
            "lastCheckedAt": update.last_checked_at.isoformat(),
        }, separators=(",", ":")).encode()
        response = self._request("PATCH", f"/internal/subscriptions/{update.subscription_id}/listings", body)
        if response.status_code == 204:
            return True
        if response.status_code == 404:
            return False
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SubscriptionsServiceUnavailableError("Subscriptions service request failed") from exc
        raise SubscriptionsServiceUnavailableError("Unexpected Subscriptions service response")

    def _request(self, method: str, path: str, body: bytes | None = None) -> httpx.Response:
        url = f"{self._base_url}{path}"
        headers = {"Content-Type": "application/json"} if body is not None else {}
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["x-correlation-id"] = correlation_id
        request = AWSRequest(method=method, url=url, data=body, headers=headers)
        credentials = self._session.get_credentials()
        if credentials is None:
            raise SubscriptionsServiceUnavailableError("AWS credentials are unavailable")
        SigV4Auth(credentials.get_frozen_credentials(), "execute-api", self._region_name).add_auth(request)
        try:
            return self._http_client.request(method, url, content=body, headers=dict(request.headers.items()))
        except httpx.RequestError as exc:
            raise SubscriptionsServiceUnavailableError("Subscriptions service request failed") from exc

    @staticmethod
    def _from_dict(data: Any) -> MonitoredSubscription:
        if not isinstance(data, dict) or not isinstance(data.get("vehicle"), dict):
            raise ValueError("Invalid monitoring subscription")
        vehicle = data["vehicle"]
        seen = data.get("seenListings")
        if not isinstance(seen, list) or not all(isinstance(value, str) and value for value in seen):
            raise ValueError("Invalid seen listings")
        return MonitoredSubscription(
            subscription_id=str(data["id"]), email=str(data["email"]),
            management_token=str(data["managementToken"]), make_id=str(data["makeId"]),
            model_id=str(data["modelId"]), version_id=str(data["versionId"]), year_id=str(data["yearId"]),
            state=str(data["state"]), city=str(data["city"]), latitude=float(data["latitude"]),
            longitude=float(data["longitude"]), radius_km=float(data["radiusKm"]),
            vehicle=MonitoredVehicle(str(vehicle["make"]), str(vehicle["model"]), str(vehicle["version"]), str(vehicle["year"])),
            seen_listing_ids=tuple(seen),
        )
