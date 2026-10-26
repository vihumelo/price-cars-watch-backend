import httpx
import pytest
from unittest.mock import Mock

from services.notifications.src.errors import EmailDeliveryError
from services.notifications.src.providers.brevo.brevo_email_provider import BrevoEmailProvider


def _http_client(response: httpx.Response) -> Mock:
    client = Mock()
    client.post.return_value = response
    return client


def _response(status_code: int, payload: object) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", "https://brevo.test/v3/smtp/email"),
    )


def test_confirmation_translates_domain_request_to_brevo_payload(confirmation_request):
    client = _http_client(_response(201, {"messageId": "brevo-message-1"}))
    provider = BrevoEmailProvider(
        api_key="test-key",
        http_client=client,
        base_url="https://brevo.test/v3",
        confirmation_template_id=4,
        new_listings_template_id=5,
        public_frontend_base_url="https://frontend.example.test",
    )

    provider.send_confirmation(confirmation_request)

    client.post.assert_called_once_with(
        "https://brevo.test/v3/smtp/email",
        headers={"accept": "application/json", "api-key": "test-key"},
        json={
            "to": [{"email": "ana@example.com"}],
            "templateId": 4,
            "params": {
                "confirmation_link": "https://frontend.example.test/confirm?subscriptionId=subscription-123&token=confirm-token"
            },
            "headers": {"idempotencyKey": "event-confirmation-123"},
        },
    )


def test_new_listings_translates_domain_notification_to_brevo_payload(new_listings_notification):
    client = _http_client(_response(201, {"messageId": "brevo-message-2"}))
    provider = BrevoEmailProvider(
        api_key="test-key",
        http_client=client,
        confirmation_template_id=4,
        new_listings_template_id=5,
        public_frontend_base_url="https://frontend.example.test",
    )

    provider.send_new_listings(new_listings_notification)

    payload = client.post.call_args.kwargs["json"]
    assert payload["templateId"] == 5
    assert payload["to"] == [{"email": "ana@example.com"}]
    assert payload["params"]["vehicle_name"] == "HONDA HR-V LX 2017"
    assert payload["params"]["unsubscribe_link"] == (
        "https://frontend.example.test/unsubscribe?subscriptionId=subscription-123&token=manage-token"
    )
    assert payload["params"]["listings"] == [{
        "id": "80851171", "title": "HONDA HR-V LX", "price": "R$ 79.990,00",
        "manufacture_year": "2017", "model_year": "2017", "odometer": "50.000",
        "transmission": "Automática", "seller_city": "Campinas",
        "seller_state": "São Paulo (SP)", "seller_type": "PJ",
        "listing_url": "https://www.webmotors.com.br/comprar/honda/hr-v/lx/4-portas/2017/80851171",
    }]


def test_provider_raises_structured_error_for_brevo_failure(confirmation_request):
    client = _http_client(_response(400, {"code": "invalid_parameter", "message": "Template is inactive"}))
    provider = BrevoEmailProvider(
        api_key="test-key",
        http_client=client,
        confirmation_template_id=4,
        new_listings_template_id=5,
        public_frontend_base_url="https://frontend.example.test",
    )

    with pytest.raises(EmailDeliveryError) as raised:
        provider.send_confirmation(confirmation_request)

    error = raised.value
    assert error.provider == "brevo"
    assert error.operation == "send_confirmation"
    assert error.status_code == 400
    assert error.provider_code == "invalid_parameter"
    assert error.provider_message == "Template is inactive"
    assert error.retryable is False
