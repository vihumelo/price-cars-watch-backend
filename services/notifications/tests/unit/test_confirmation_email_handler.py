import json
from unittest.mock import Mock

from services.notifications.src.handlers import confirmation_email


def test_handler_processes_sns_enveloped_confirmation_record(monkeypatch):
    service = Mock()
    monkeypatch.setattr(confirmation_email, "_confirmation_email_service", lambda: service)
    event = {"Records": [{"messageId": "message-1", "body": json.dumps({"Type": "Notification", "Message": json.dumps({"eventId": "event-1", "subscriptionId": "sub-1", "email": "ana@example.com", "confirmationToken": "token"})})}]}

    response = confirmation_email.handler(event, Mock())

    assert response == {"batchItemFailures": []}
    assert service.send_confirmation_email.call_args.args[0].confirmation_token == "token"


def test_handler_marks_invalid_confirmation_record_for_retry(monkeypatch):
    monkeypatch.setattr(confirmation_email, "_confirmation_email_service", lambda: Mock())

    response = confirmation_email.handler({"Records": [{"messageId": "message-1", "body": "not-json"}]}, Mock())

    assert response == {"batchItemFailures": [{"itemIdentifier": "message-1"}]}
