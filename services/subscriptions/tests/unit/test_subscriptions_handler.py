import json
from unittest.mock import Mock

import pytest

from services.subscriptions.src.handlers import subscriptions


@pytest.fixture
def context() -> Mock:
    return Mock(aws_request_id="request-123")


def test_handler_creates_subscription_with_location(monkeypatch, context):
    service = Mock()
    monkeypatch.setattr(subscriptions, "_create_service", lambda: service)
    metric = Mock()
    monkeypatch.setattr(subscriptions, "emit_metric", metric)
    event = {"routeKey": "POST /subscriptions", "body": json.dumps({
        "email": "ana@example.com", "makeId": "HONDA", "modelId": "HR-V", "versionId": "LX", "yearId": "2017",
        "state": "São Paulo", "city": "Valinhos", "latitude": -22.97056, "longitude": -46.99583, "radiusKm": 25,
    })}

    response = subscriptions.handler(event, context)

    assert response["statusCode"] == 202
    service.create_subscription.assert_called_once_with(
        email="ana@example.com", make_id="HONDA", model_id="HR-V", version_id="LX", year_id="2017",
        state="São Paulo", city="Valinhos", latitude=-22.97056, longitude=-46.99583, radius_km=25.0,
    )
    metric.assert_any_call("SubscriptionsCreated")


def test_handler_rejects_subscription_without_geographic_criteria(context):
    response = subscriptions.handler({"routeKey": "POST /subscriptions", "body": json.dumps({"email": "ana@example.com"})}, context)
    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "INVALID_REQUEST"


def test_handler_accepts_zero_radius(monkeypatch, context):
    service = Mock()
    monkeypatch.setattr(subscriptions, "_create_service", lambda: service)
    event = {"routeKey": "POST /subscriptions", "body": json.dumps({
        "email": "ana@example.com", "makeId": "HONDA", "modelId": "HR-V", "versionId": "LX", "yearId": "2017",
        "state": "São Paulo", "city": "Valinhos", "latitude": -22.97056, "longitude": -46.99583, "radiusKm": 0,
    })}

    response = subscriptions.handler(event, context)

    assert response["statusCode"] == 202
    assert service.create_subscription.call_args.kwargs["radius_km"] == 0.0


def test_handler_records_confirmation_success(monkeypatch, context):
    service = Mock()
    metric = Mock()
    monkeypatch.setattr(subscriptions, "_confirm_service", lambda: service)
    monkeypatch.setattr(subscriptions, "emit_metric", metric)

    response = subscriptions.handler({
        "routeKey": "GET /subscriptions/{subscriptionId}/confirm",
        "pathParameters": {"subscriptionId": "subscription-123"},
        "queryStringParameters": {"token": "confirm-token"},
    }, context)

    assert response["statusCode"] == 200
    metric.assert_any_call("SubscriptionsConfirmed")


def test_handler_records_confirmation_failure(monkeypatch, context):
    metric = Mock()
    monkeypatch.setattr(subscriptions, "emit_metric", metric)

    response = subscriptions.handler({
        "routeKey": "GET /subscriptions/{subscriptionId}/confirm",
        "pathParameters": {"subscriptionId": "subscription-123"},
    }, context)

    assert response["statusCode"] == 400
    metric.assert_any_call("SubscriptionsConfirmationFailed")


def test_handler_records_cancel_and_delete(monkeypatch, context):
    service = Mock()
    metric = Mock()
    monkeypatch.setattr(subscriptions, "_cancel_service", lambda: service)
    monkeypatch.setattr(subscriptions, "emit_metric", metric)

    response = subscriptions.handler({
        "routeKey": "DELETE /subscriptions/{subscriptionId}",
        "pathParameters": {"subscriptionId": "subscription-123"},
        "queryStringParameters": {"token": "management-token"},
    }, context)

    assert response["statusCode"] == 204
    metric.assert_any_call("SubscriptionsCancelled")
    metric.assert_any_call("SubscriptionsDeleted")


def test_handler_rejects_invalid_seen_listings_update(context):
    response = subscriptions.handler({
        "routeKey": "PATCH /internal/subscriptions/{subscriptionId}/listings",
        "pathParameters": {"subscriptionId": "subscription-123"},
        "body": json.dumps({"seenListings": ["ok", ""], "lastCheckedAt": "2026-01-03T10:00:00+00:00"}),
    }, context)
    assert response["statusCode"] == 400
