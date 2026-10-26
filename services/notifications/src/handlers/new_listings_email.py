from functools import cache
from time import perf_counter
from typing import Any

from services.shared.observability import bind_context, clear_context, configure_logging, emit_metric, get_or_create_correlation_id, metrics
from ..errors import EmailDeliveryError
from ..models.new_listings_notification import ListingEmailItem, NewListingsNotification
from ..providers.email_provider_factory import build_email_provider
from ..services.send_new_listings_email_service import SendNewListingsEmailService
from .queue_message import correlation_id_from_record, event_body_from_record, receive_attempt

logger = configure_logging("notifications")


@metrics.log_metrics
def handler(event: dict[str, Any], context: Any) -> dict[str, list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    for record in event.get("Records", []):
        message_id = str(record["messageId"])
        started_at = perf_counter()
        clear_context()
        bind_context(correlation_id=get_or_create_correlation_id(correlation_id_from_record(record)), message_id=message_id, **_request_context(context))
        try:
            notification = _notification_from_record(record)
            _new_listings_email_service().send_new_listings_email(notification)
            emit_metric("NotificationsSent")
            logger.info("notification_processed", operation="send_new_listings_email", event_id=notification.event_id, subscription_id=notification.subscription_id, listings_count=len(notification.listings), attempt=receive_attempt(record))
        except EmailDeliveryError as exc:
            emit_metric("NotificationDeliveryFailures")
            logger.exception("notification_processing_failed", operation="send_new_listings_email", message_id=message_id, error_type=type(exc).__name__, provider=exc.provider, provider_operation=exc.operation, status_code=exc.status_code, provider_code=exc.provider_code, provider_message=exc.provider_message, retryable=exc.retryable, attempt=receive_attempt(record), duration_ms=_duration_ms(started_at))
            failures.append({"itemIdentifier": message_id})
        except Exception as exc:
            emit_metric("NotificationDeliveryFailures")
            logger.exception("notification_processing_failed", operation="send_new_listings_email", message_id=message_id, error_type=type(exc).__name__, attempt=receive_attempt(record), duration_ms=_duration_ms(started_at))
            failures.append({"itemIdentifier": message_id})
        finally:
            clear_context()
    return {"batchItemFailures": failures}


def _notification_from_record(record: dict[str, Any]) -> NewListingsNotification:
    body = event_body_from_record(record)
    try:
        vehicle = body["vehicle"]
        location = body["location"]
        listings = body["listings"]
        if not isinstance(vehicle, dict) or not isinstance(location, dict) or not isinstance(listings, list) or not listings:
            raise ValueError("Invalid new listings email message")
        items = tuple(_listing_from_dict(item) for item in listings)
        return NewListingsNotification(
            event_id=str(body["eventId"]), subscription_id=str(body["subscriptionId"]), email=str(body["email"]),
            management_token=str(body["managementToken"]),
            vehicle_name=f"{vehicle['make']} {vehicle['model']} {vehicle['version']} {vehicle['year']}",
            location=f"{location['city']} - {location['state']}, raio de {location['radiusKm']} km",
            listings=items,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid new listings email message") from exc


def _listing_from_dict(data: Any) -> ListingEmailItem:
    if not isinstance(data, dict):
        raise ValueError("Invalid listing")
    odometer = data.get("odometer")
    if odometer is not None and (isinstance(odometer, bool) or not isinstance(odometer, int)):
        raise ValueError("Invalid listing odometer")
    return ListingEmailItem(
        listing_id=str(data["id"]), title=str(data["title"]), price=float(data["price"]),
        manufacture_year=str(data["manufactureYear"]), model_year=str(data["modelYear"]), odometer=odometer,
        transmission=_optional_string(data.get("transmission")), seller_city=_optional_string(data.get("sellerCity")),
        seller_state=_optional_string(data.get("sellerState")), seller_type=_optional_string(data.get("sellerType")),
        listing_url=_optional_string(data.get("listingUrl")),
    )


def _optional_string(value: Any) -> str | None:
    return str(value) if value is not None else None


def _duration_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 2)


def _request_context(context: Any) -> dict[str, str]:
    request_id = getattr(context, "aws_request_id", None)
    return {"request_id": request_id} if isinstance(request_id, str) and request_id else {}


@cache
def _new_listings_email_service() -> SendNewListingsEmailService:
    return SendNewListingsEmailService(build_email_provider())
