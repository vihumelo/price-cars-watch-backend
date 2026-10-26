import httpx
import pytest
from unittest.mock import Mock

from services.notifications.src.errors import EmailDeliveryError
from services.notifications.src.providers.mailjet.mailjet_email_provider import MailjetEmailProvider


def _http_client(response: httpx.Response) -> Mock:
    client = Mock()
    client.post.return_value = response
    return client


def _response(status_code: int, payload: object) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", "https://mailjet.test/v3.1/send"),
    )


def _provider(client: Mock) -> MailjetEmailProvider:
    return MailjetEmailProvider(
        api_key="test-api-key",
        secret_key="test-secret-key",
        http_client=client,
        base_url="https://mailjet.test/v3.1",
        confirmation_template_id=4,
        new_listings_template_id=5,
        public_frontend_base_url="https://frontend.example.test",
        sender_email="noreply@example.com",
        sender_name="Prices Car Watch",
    )


def test_confirmation_translates_domain_request_to_mailjet_payload(confirmation_request):
    client = _http_client(_response(200, {"Messages": [{"Status": "success"}]}))

    _provider(client).send_confirmation(confirmation_request)

    client.post.assert_called_once_with(
        "https://mailjet.test/v3.1/send",
        auth=("test-api-key", "test-secret-key"),
        headers={"accept": "application/json", "content-type": "application/json"},
        json={
            "Messages": [{
                "From": {"Email": "noreply@example.com", "Name": "Prices Car Watch"},
                "To": [{"Email": "ana@example.com"}],
                "TemplateID": 4,
                "TemplateLanguage": True,
                "Variables": {
                    "confirmation_link": "https://frontend.example.test/confirm?subscriptionId=subscription-123&token=confirm-token"
                },
                "CustomID": "event-confirmation-123",
            }]
        },
    )


def test_new_listings_translates_domain_notification_to_mailjet_payload(new_listings_notification):
    client = _http_client(_response(200, {"Messages": [{"Status": "success"}]}))

    _provider(client).send_new_listings(new_listings_notification)

    payload = client.post.call_args.kwargs["json"]["Messages"][0]
    assert payload["TemplateID"] == 5
    assert payload["TemplateLanguage"] is True
    assert payload["Variables"]["vehicle_name"] == "HONDA HR-V LX 2017"
    assert payload["Variables"]["unsubscribe_link"] == (
        "https://frontend.example.test/unsubscribe?subscriptionId=subscription-123&token=manage-token"
    )
    assert payload["Variables"]["listings"] == [{
        "id": "80851171", "title": "HONDA HR-V LX", "price": "R$ 79.990,00",
        "manufacture_year": "2017", "model_year": "2017", "odometer": "50.000",
        "transmission": "Automática", "seller_city": "Campinas",
        "seller_state": "São Paulo (SP)", "seller_type": "PJ",
        "listing_url": "https://www.webmotors.com.br/comprar/honda/hr-v/lx/4-portas/2017/80851171",
    }]


def test_provider_raises_structured_error_for_mailjet_failure(confirmation_request):
    client = _http_client(_response(401, {"ErrorIdentifier": "mj-unauthorized", "ErrorMessage": "Unauthorized"}))

    with pytest.raises(EmailDeliveryError) as raised:
        _provider(client).send_confirmation(confirmation_request)

    error = raised.value
    assert error.provider == "mailjet"
    assert error.operation == "send_confirmation"
    assert error.status_code == 401
    assert error.provider_code == "mj-unauthorized"
    assert error.provider_message == "Unauthorized"
    assert error.retryable is False
