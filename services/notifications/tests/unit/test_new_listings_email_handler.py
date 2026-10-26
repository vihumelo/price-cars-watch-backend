import json
from unittest.mock import Mock

from services.notifications.src.handlers import new_listings_email


def test_handler_processes_new_listings_record(monkeypatch):
    service = Mock()
    monkeypatch.setattr(new_listings_email, "_new_listings_email_service", lambda: service)
    payload = {
        "eventId": "event-1", "subscriptionId": "sub-1", "email": "ana@example.com", "managementToken": "manage-token",
        "vehicle": {"make": "HONDA", "model": "HR-V", "version": "LX", "year": "2017"},
        "location": {"city": "Valinhos", "state": "São Paulo", "radiusKm": 25},
        "listings": [{"id": "listing-1", "title": "HONDA HR-V LX", "price": 79990, "manufactureYear": "2017", "modelYear": "2017", "odometer": 50000, "transmission": "Automática", "sellerCity": "Campinas", "sellerState": "São Paulo (SP)", "sellerType": "PJ", "listingUrl": "https://www.webmotors.com.br/comprar/honda/hr-v/lx/4-portas/2017/listing-1"}],
    }

    response = new_listings_email.handler({"Records": [{"messageId": "message-1", "body": json.dumps(payload)}]}, Mock())

    assert response == {"batchItemFailures": []}
    notification = service.send_new_listings_email.call_args.args[0]
    assert notification.vehicle_name == "HONDA HR-V LX 2017"
    assert notification.listings[0].listing_id == "listing-1"
    assert notification.listings[0].listing_url.endswith("/listing-1")


def test_handler_retries_record_when_delivery_fails(monkeypatch):
    service = Mock()
    service.send_new_listings_email.side_effect = RuntimeError("Brevo unavailable")
    monkeypatch.setattr(new_listings_email, "_new_listings_email_service", lambda: service)

    response = new_listings_email.handler({"Records": [{"messageId": "message-1", "body": "{}"}]}, Mock())

    assert response == {"batchItemFailures": [{"itemIdentifier": "message-1"}]}
