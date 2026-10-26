import os
from functools import cache
from time import perf_counter
from typing import Any
from uuid import uuid4

from services.shared.observability import (
    bind_context, clear_context, configure_logging, emit_metric,
    get_or_create_correlation_id, metrics,
)
from ..providers.sqs_new_listings_publisher import SqsNewListingsPublisher
from ..providers.subscriptions_api_client import SubscriptionsApiClient
from ..providers.vehicles_api_listings_lookup import VehiclesApiListingsLookup
from ..services.monitoring_service import MonitoringService

logger = configure_logging("monitoring")


@metrics.log_metrics
def handler(event: dict[str, Any], context: Any) -> dict[str, str]:
    run_id = event.get("id")
    if not isinstance(run_id, str) or not run_id:
        run_id = str(uuid4())
    clear_context()
    bind_context(correlation_id=get_or_create_correlation_id(_correlation_id(event)), run_id=run_id, **_request_context(context))
    started_at = perf_counter()
    try:
        summary = _monitoring_service().run(run_id)
    except Exception as exc:
        emit_metric("MonitoringRunsFailed")
        logger.exception("monitoring_run_failed", run_id=run_id, error_type=type(exc).__name__, duration_ms=_duration_ms(started_at))
        raise
    else:
        emit_metric("MonitoringRunsCompleted")
        emit_metric("NewListingsDetected", value=summary["new_listings_detected"])
        emit_metric("NotificationsPublished", value=summary["notifications_published"])
        logger.info("monitoring_run_completed", run_id=run_id, **summary, duration_ms=_duration_ms(started_at))
        return {"status": "completed"}
    finally:
        clear_context()


def _duration_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 2)


def _correlation_id(event: dict[str, Any]) -> str | None:
    for name in ("correlationId", "correlation_id"):
        value = event.get(name)
        if isinstance(value, str):
            return value
    return None


def _request_context(context: Any) -> dict[str, str]:
    request_id = getattr(context, "aws_request_id", None)
    return {"request_id": request_id} if isinstance(request_id, str) and request_id else {}


@cache
def _monitoring_service() -> MonitoringService:
    subscriptions_api = SubscriptionsApiClient()
    return MonitoringService(
        subscription_reader=subscriptions_api,
        subscription_listings_updater=subscriptions_api,
        vehicle_listings_lookup=VehiclesApiListingsLookup(),
        new_listings_publisher=SqsNewListingsPublisher(os.environ["NEW_LISTINGS_QUEUE_URL"]),
    )
