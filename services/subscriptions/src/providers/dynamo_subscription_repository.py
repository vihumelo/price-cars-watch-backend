import os
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import boto3
from boto3.dynamodb.conditions import Key

from ..models.subscription import Subscription, SubscriptionStatus, SubscriptionVehicle
from ..ports.subscription_repository import SubscriptionRepository


class DynamoSubscriptionRepository(SubscriptionRepository):
    """Persist Webmotors subscriptions in the same DynamoDB shape as FIPE Watch."""

    DEFAULT_TABLE_NAME = "prices-car-watch-subscriptions"
    DEFAULT_SUBSCRIPTION_KEY_INDEX_NAME = "subscriptionKey-index"
    DEFAULT_STATUS_INDEX_NAME = "status-index"

    def __init__(
        self,
        table_name: str | None = None,
        subscription_key_index_name: str | None = None,
        status_index_name: str | None = None,
        dynamodb_resource: Any | None = None,
    ) -> None:
        dynamodb = cast(Any, dynamodb_resource or boto3.resource("dynamodb"))
        self._table = dynamodb.Table(
            table_name or os.getenv("SUBSCRIPTIONS_TABLE_NAME", self.DEFAULT_TABLE_NAME)
        )
        self._subscription_key_index_name = subscription_key_index_name or os.getenv(
            "SUBSCRIPTIONS_SUBSCRIPTION_KEY_INDEX_NAME",
            self.DEFAULT_SUBSCRIPTION_KEY_INDEX_NAME,
        )
        self._status_index_name = status_index_name or os.getenv(
            "SUBSCRIPTIONS_STATUS_INDEX_NAME", self.DEFAULT_STATUS_INDEX_NAME
        )

    def get_by_id(self, subscription_id: str) -> Subscription | None:
        item = self._table.get_item(Key={"subscriptionId": subscription_id}).get("Item")
        return self._from_item(item) if item else None

    def find_by_subscription_key(self, subscription_key: str) -> list[Subscription]:
        response = self._table.query(
            IndexName=self._subscription_key_index_name,
            KeyConditionExpression=Key("subscriptionKey").eq(subscription_key),
        )
        return [self._from_item(item) for item in response.get("Items", [])]

    def list_active(self) -> list[Subscription]:
        items: list[dict[str, Any]] = []
        query: dict[str, Any] = {
            "IndexName": self._status_index_name,
            "KeyConditionExpression": Key("status").eq(SubscriptionStatus.ACTIVE),
        }
        while True:
            response = self._table.query(**query)
            items.extend(response.get("Items", []))
            if "LastEvaluatedKey" not in response:
                break
            query["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        return [self._from_item(item) for item in items]

    def save(self, subscription: Subscription) -> None:
        self._table.put_item(Item=self._to_item(subscription))

    def update(self, subscription: Subscription) -> None:
        self._table.put_item(Item=self._to_item(subscription))

    @staticmethod
    def _to_item(subscription: Subscription) -> dict[str, Any]:
        item: dict[str, Any] = {
            "subscriptionId": subscription.subscription_id,
            "subscriptionKey": subscription.subscription_key,
            "email": subscription.email,
            "makeId": subscription.make_id,
            "modelId": subscription.model_id,
            "versionId": subscription.version_id,
            "yearId": subscription.year_id,
            "state": subscription.state,
            "city": subscription.city,
            "latitude": Decimal(str(subscription.latitude)),
            "longitude": Decimal(str(subscription.longitude)),
            "radiusKm": Decimal(str(subscription.radius_km)),
            "status": subscription.status.value,
            "managementToken": subscription.management_token,
            "createdAt": subscription.created_at.isoformat(),
            "seenListings": list(subscription.seen_listing_ids),
        }
        optional = {
            "confirmationToken": subscription.confirmation_token,
            "confirmedAt": subscription.confirmed_at.isoformat() if subscription.confirmed_at else None,
            "cancelledAt": subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            "lastCheckedAt": subscription.last_checked_at.isoformat() if subscription.last_checked_at else None,
            "baselineCapturedAt": subscription.baseline_captured_at.isoformat() if subscription.baseline_captured_at else None,
        }
        item.update({key: value for key, value in optional.items() if value is not None})
        if subscription.vehicle:
            item["vehicle"] = {
                "make": subscription.vehicle.make,
                "model": subscription.vehicle.model,
                "version": subscription.vehicle.version,
                "year": subscription.vehicle.year,
            }
        return item

    @staticmethod
    def _from_item(item: dict[str, Any]) -> Subscription:
        vehicle = item.get("vehicle")
        return Subscription(
            subscription_id=str(item["subscriptionId"]),
            subscription_key=str(item["subscriptionKey"]),
            email=str(item["email"]),
            make_id=str(item["makeId"]),
            model_id=str(item["modelId"]),
            version_id=str(item["versionId"]),
            year_id=str(item["yearId"]),
            state=str(item["state"]), city=str(item["city"]),
            latitude=float(item["latitude"]), longitude=float(item["longitude"]),
            radius_km=float(item["radiusKm"]),
            status=SubscriptionStatus(str(item["status"])),
            management_token=str(item["managementToken"]),
            created_at=datetime.fromisoformat(str(item["createdAt"])),
            confirmation_token=item.get("confirmationToken"),
            vehicle=SubscriptionVehicle(
                make=str(vehicle["make"]), model=str(vehicle["model"]),
                version=str(vehicle["version"]), year=str(vehicle["year"]),
            ) if isinstance(vehicle, dict) else None,
            seen_listing_ids=tuple(str(value) for value in item.get("seenListings", [])),
            confirmed_at=_optional_datetime(item.get("confirmedAt")),
            cancelled_at=_optional_datetime(item.get("cancelledAt")),
            last_checked_at=_optional_datetime(item.get("lastCheckedAt")),
            baseline_captured_at=_optional_datetime(item.get("baselineCapturedAt")),
        )


def _optional_datetime(value: Any) -> datetime | None:
    return datetime.fromisoformat(str(value)) if value is not None else None
