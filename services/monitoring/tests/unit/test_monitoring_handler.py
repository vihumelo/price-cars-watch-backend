from unittest.mock import Mock

import pytest

from services.monitoring.src.handlers import monitoring


def test_handler_uses_event_id_for_monitoring_run(monkeypatch):
    service = Mock()
    service.run.return_value = {"subscriptions_checked": 1, "listing_searches": 1, "new_listings_detected": 2, "notifications_published": 1}
    monkeypatch.setattr(monitoring, "_monitoring_service", lambda: service)

    response = monitoring.handler({"id": "scheduled-run-123"}, Mock())

    assert response == {"status": "completed"}
    service.run.assert_called_once_with("scheduled-run-123")


def test_handler_propagates_failure_for_eventbridge_retry(monkeypatch):
    service = Mock()
    service.run.side_effect = RuntimeError("Vehicles unavailable")
    monkeypatch.setattr(monitoring, "_monitoring_service", lambda: service)

    with pytest.raises(RuntimeError, match="Vehicles unavailable"):
        monitoring.handler({"id": "scheduled-run-123"}, Mock())
