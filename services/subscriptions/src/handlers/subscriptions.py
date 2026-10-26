from functools import cache
import os
from datetime import datetime
from typing import Any

from services.shared.api_gateway import is_non_empty_string, json_body, path_parameter, query_parameter, route_key
from services.shared.http import error_response, json_response
from services.shared.observability import bind_context, clear_context, configure_logging, emit_metric, get_or_create_correlation_id, metrics

from ..errors import (
    InvalidConfirmationLinkError,
    SubscriptionAccessDeniedError,
    VehicleListingsNotFoundError,
    VehicleListingsServiceUnavailableError,
)
from ..models.monitoring_subscription import MonitoringSubscription
from ..models.subscription import Subscription
from ..models.subscription_listings_update import SubscriptionListingsUpdate
from ..providers.dynamo_subscription_repository import DynamoSubscriptionRepository
from ..providers.sqs_confirmation_email_publisher import SqsConfirmationEmailPublisher
from ..providers.vehicles_api_listings_lookup import VehiclesApiListingsLookup
from ..services.cancel_subscription_service import CancelSubscriptionService
from ..services.confirm_subscription_service import ConfirmSubscriptionService
from ..services.create_subscription_service import CreateSubscriptionService
from ..services.get_subscription_service import GetSubscriptionService
from ..services.list_monitoring_subscriptions_service import ListMonitoringSubscriptionsService
from ..services.update_subscription_listings_service import UpdateSubscriptionListingsService

logger = configure_logging("subscriptions")


@metrics.log_metrics
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    clear_context()
    bind_context(
        correlation_id=get_or_create_correlation_id(_correlation_id(event)),
        **_request_context(context),
    )
    try:
        key = route_key(event)
        if key == "POST /subscriptions":
            return create_subscription_handler(event)
        if key == "GET /subscriptions/{subscriptionId}/confirm":
            return confirm_subscription_handler(event)
        if key == "GET /subscriptions/{subscriptionId}":
            return get_subscription_handler(event)
        if key == "DELETE /subscriptions/{subscriptionId}":
            return cancel_subscription_handler(event)
        if key == "GET /internal/subscriptions/monitoring":
            return list_monitoring_subscriptions_handler()
        if key == "PATCH /internal/subscriptions/{subscriptionId}/listings":
            return update_subscription_listings_handler(event)
        return error_response(404, "ROUTE_NOT_FOUND", "Route not found")
    finally:
        clear_context()


def create_subscription_handler(event: dict[str, Any]) -> dict[str, Any]:
    data = _parse_create(event)
    if data is None:
        return error_response(400, "INVALID_REQUEST", "Invalid request")
    try:
        _create_service().create_subscription(**data)
        emit_metric("SubscriptionsCreated")
        return json_response(202, {"status": "accepted"})
    except Exception:
        logger.exception("subscription_request_failed", operation="create_subscription")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")


def confirm_subscription_handler(event: dict[str, Any]) -> dict[str, Any]:
    subscription_id = path_parameter(event, "subscriptionId")
    token = query_parameter(event, "token")
    if not subscription_id or not token:
        emit_metric("SubscriptionsConfirmationFailed")
        return error_response(400, "INVALID_CONFIRMATION_LINK", "Invalid or expired confirmation link")
    try:
        _confirm_service().confirm_subscription(subscription_id, token)
        emit_metric("SubscriptionsConfirmed")
        return json_response(200, {"id": subscription_id, "status": "active"})
    except InvalidConfirmationLinkError:
        emit_metric("SubscriptionsConfirmationFailed")
        return error_response(400, "INVALID_CONFIRMATION_LINK", "Invalid or expired confirmation link")
    except VehicleListingsNotFoundError:
        emit_metric("SubscriptionsConfirmationFailed")
        return error_response(400, "VEHICLE_NOT_FOUND", "Vehicle listings not found")
    except VehicleListingsServiceUnavailableError as exc:
        emit_metric("SubscriptionsConfirmationFailed")
        logger.error(
            "subscription_request_failed",
            operation="confirm_subscription",
            error_code="VEHICLES_SERVICE_UNAVAILABLE",
            provider="vehicles_api",
            provider_status_code=exc.status_code,
            provider_request_id=exc.provider_request_id,
            error=str(exc),
        )
        return error_response(502, "VEHICLES_SERVICE_UNAVAILABLE", "Vehicles service is unavailable")
    except Exception:
        emit_metric("SubscriptionsConfirmationFailed")
        logger.exception("subscription_request_failed", operation="confirm_subscription")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")


def get_subscription_handler(event: dict[str, Any]) -> dict[str, Any]:
    subscription_id = path_parameter(event, "subscriptionId")
    token = query_parameter(event, "token")
    if not subscription_id or not token:
        return error_response(401, "INVALID_MANAGEMENT_TOKEN", "Invalid management token")
    try:
        subscription = _get_service().get_subscription(subscription_id, token)
        return json_response(200, _subscription_to_dict(subscription))
    except SubscriptionAccessDeniedError:
        return error_response(401, "INVALID_MANAGEMENT_TOKEN", "Invalid management token")
    except Exception:
        logger.exception("subscription_request_failed", operation="get_subscription")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")


def cancel_subscription_handler(event: dict[str, Any]) -> dict[str, Any]:
    subscription_id = path_parameter(event, "subscriptionId")
    token = query_parameter(event, "token")
    if not subscription_id or not token:
        return error_response(401, "INVALID_MANAGEMENT_TOKEN", "Invalid management token")
    try:
        _cancel_service().cancel_subscription(subscription_id, token)
        emit_metric("SubscriptionsCancelled")
        # DELETE is the public operation; the record is retained as cancelled in DynamoDB.
        emit_metric("SubscriptionsDeleted")
        return {"statusCode": 204, "headers": {}, "body": ""}
    except SubscriptionAccessDeniedError:
        return error_response(401, "INVALID_MANAGEMENT_TOKEN", "Invalid management token")
    except Exception:
        logger.exception("subscription_request_failed", operation="cancel_subscription")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")


def list_monitoring_subscriptions_handler() -> dict[str, Any]:
    try:
        subscriptions = _monitoring_service().list_monitoring_subscriptions()
        return json_response(200, [_monitoring_to_dict(item) for item in subscriptions])
    except Exception:
        logger.exception("subscription_request_failed", operation="list_monitoring_subscriptions")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")


def update_subscription_listings_handler(event: dict[str, Any]) -> dict[str, Any]:
    update = _parse_listings_update(event)
    if update is None:
        return error_response(400, "INVALID_REQUEST", "Invalid request")
    try:
        if not _update_listings_service().update_subscription_listings(update):
            return error_response(404, "SUBSCRIPTION_NOT_FOUND", "Subscription not found")
        return {"statusCode": 204, "headers": {}, "body": ""}
    except Exception:
        logger.exception("subscription_request_failed", operation="update_subscription_listings")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")


def _parse_create(event: dict[str, Any]) -> dict[str, Any] | None:
    body = json_body(event)
    if not isinstance(body, dict):
        return None
    field_names = {
        "email": "email", "makeId": "make_id", "modelId": "model_id",
        "versionId": "version_id", "yearId": "year_id", "state": "state", "city": "city",
    }
    result: dict[str, Any] = {}
    for source, target in field_names.items():
        value = body.get(source)
        if not is_non_empty_string(value):
            return None
        result[target] = value.strip()
    for source, target in (("latitude", "latitude"), ("longitude", "longitude"), ("radiusKm", "radius_km")):
        value = body.get(source)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        result[target] = float(value)
    if not (-90 <= result["latitude"] <= 90 and -180 <= result["longitude"] <= 180 and result["radius_km"] >= 0):
        return None
    return result


def _parse_listings_update(event: dict[str, Any]) -> SubscriptionListingsUpdate | None:
    subscription_id = path_parameter(event, "subscriptionId")
    body = json_body(event)
    if not subscription_id or not isinstance(body, dict) or not isinstance(body.get("seenListings"), list):
        return None
    seen = body["seenListings"]
    checked_at = body.get("lastCheckedAt")
    if not all(is_non_empty_string(value) for value in seen) or not is_non_empty_string(checked_at):
        return None
    try:
        timestamp = datetime.fromisoformat(checked_at)
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        return None
    return SubscriptionListingsUpdate(subscription_id, tuple(seen), timestamp)


def _subscription_to_dict(subscription: Subscription) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": subscription.subscription_id,
        "status": subscription.status.value,
        "email": subscription.email,
        "seenListings": list(subscription.seen_listing_ids),
    }
    if subscription.vehicle:
        result["vehicle"] = {
            "make": subscription.vehicle.make, "model": subscription.vehicle.model,
            "version": subscription.vehicle.version, "year": subscription.vehicle.year,
        }
    for name, value in (("confirmedAt", subscription.confirmed_at), ("cancelledAt", subscription.cancelled_at),
                        ("lastCheckedAt", subscription.last_checked_at), ("baselineCapturedAt", subscription.baseline_captured_at)):
        if value:
            result[name] = value.isoformat()
    return result


def _monitoring_to_dict(item: MonitoringSubscription) -> dict[str, Any]:
    return {
        "id": item.subscription_id, "email": item.email, "managementToken": item.management_token,
        "makeId": item.make_id, "modelId": item.model_id, "versionId": item.version_id,
        "yearId": item.year_id, "state": item.state, "city": item.city,
        "latitude": item.latitude, "longitude": item.longitude, "radiusKm": item.radius_km,
        "seenListings": list(item.seen_listing_ids),
        "vehicle": {"make": item.vehicle.make, "model": item.vehicle.model,
                    "version": item.vehicle.version, "year": item.vehicle.year},
    }


def _correlation_id(event: dict[str, Any]) -> str | None:
    headers = event.get("headers")
    if not isinstance(headers, dict):
        return None
    return next((value for name, value in headers.items()
                 if str(name).lower() == "x-correlation-id" and isinstance(value, str)), None)


def _request_context(context: Any) -> dict[str, str]:
    request_id = getattr(context, "aws_request_id", None)
    return {"request_id": request_id} if isinstance(request_id, str) and request_id else {}


@cache
def _repository() -> DynamoSubscriptionRepository:
    return DynamoSubscriptionRepository()


@cache
def _create_service() -> CreateSubscriptionService:
    return CreateSubscriptionService(_repository(), _confirmation_publisher())


@cache
def _confirmation_publisher() -> SqsConfirmationEmailPublisher:
    return SqsConfirmationEmailPublisher(os.environ["CONFIRMATION_EMAIL_QUEUE_URL"])


@cache
def _confirm_service() -> ConfirmSubscriptionService:
    return ConfirmSubscriptionService(_repository(), VehiclesApiListingsLookup())


@cache
def _get_service() -> GetSubscriptionService:
    return GetSubscriptionService(_repository())


@cache
def _cancel_service() -> CancelSubscriptionService:
    return CancelSubscriptionService(_repository())


@cache
def _monitoring_service() -> ListMonitoringSubscriptionsService:
    return ListMonitoringSubscriptionsService(_repository())


@cache
def _update_listings_service() -> UpdateSubscriptionListingsService:
    return UpdateSubscriptionListingsService(_repository())
