from functools import cache
from time import perf_counter
from typing import Any

from services.shared.observability import bind_context, clear_context, configure_logging, emit_metric, get_or_create_correlation_id, metrics
from ..models.confirmation_email_request import ConfirmationEmailRequest
from ..errors import EmailDeliveryError
from ..providers.email_provider_factory import build_email_provider
from ..services.send_confirmation_email_service import SendConfirmationEmailService
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
            request = _request_from_record(record)
            _confirmation_email_service().send_confirmation_email(request)
            emit_metric("NotificationsSent")
            logger.info("notification_processed", operation="send_confirmation_email", event_id=request.event_id, subscription_id=request.subscription_id, attempt=receive_attempt(record))
        except EmailDeliveryError as exc:
            emit_metric("NotificationDeliveryFailures")
            logger.exception("notification_processing_failed", operation="send_confirmation_email", message_id=message_id, error_type=type(exc).__name__, provider=exc.provider, provider_operation=exc.operation, status_code=exc.status_code, provider_code=exc.provider_code, provider_message=exc.provider_message, retryable=exc.retryable, attempt=receive_attempt(record), duration_ms=_duration_ms(started_at))
            failures.append({"itemIdentifier": message_id})
        except Exception as exc:
            emit_metric("NotificationDeliveryFailures")
            logger.exception("notification_processing_failed", operation="send_confirmation_email", message_id=message_id, error_type=type(exc).__name__, attempt=receive_attempt(record), duration_ms=_duration_ms(started_at))
            failures.append({"itemIdentifier": message_id})
        finally:
            clear_context()
    return {"batchItemFailures": failures}


def _request_from_record(record: dict[str, Any]) -> ConfirmationEmailRequest:
    body = event_body_from_record(record)
    try:
        return ConfirmationEmailRequest(event_id=str(body["eventId"]), subscription_id=str(body["subscriptionId"]), email=str(body["email"]), confirmation_token=str(body["confirmationToken"]))
    except (KeyError, TypeError) as exc:
        raise ValueError("Invalid confirmation email message") from exc


def _duration_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 2)


def _request_context(context: Any) -> dict[str, str]:
    request_id = getattr(context, "aws_request_id", None)
    return {"request_id": request_id} if isinstance(request_id, str) and request_id else {}


@cache
def _confirmation_email_service() -> SendConfirmationEmailService:
    return SendConfirmationEmailService(build_email_provider())
