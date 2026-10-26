import os
from typing import TypedDict
from urllib.parse import quote

import httpx

from ...errors import EmailDeliveryError
from ...models.confirmation_email_request import ConfirmationEmailRequest
from ...models.new_listings_notification import ListingEmailItem, NewListingsNotification
from ...ports.email_provider import EmailProvider


class MailjetEmailProvider(EmailProvider):
    """Mailjet adapter for transactional template emails."""

    DEFAULT_BASE_URL = "https://api.mailjet.com/v3.1"
    DEFAULT_TIMEOUT = 10.0

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        http_client: httpx.Client | None = None,
        base_url: str | None = None,
        confirmation_template_id: int | None = None,
        new_listings_template_id: int | None = None,
        public_frontend_base_url: str | None = None,
        sender_email: str | None = None,
        sender_name: str | None = None,
    ) -> None:
        self._http_client = http_client or httpx.Client(timeout=self.DEFAULT_TIMEOUT)
        self._api_key = api_key
        self._secret_key = secret_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._confirmation_template_id = confirmation_template_id or int(
            os.environ["MAILJET_CONFIRMATION_TEMPLATE_ID"]
        )
        self._new_listings_template_id = new_listings_template_id or int(
            os.environ["MAILJET_NEW_LISTINGS_TEMPLATE_ID"]
        )
        self._public_frontend_base_url = (
            public_frontend_base_url or os.environ["PUBLIC_FRONTEND_BASE_URL"]
        ).rstrip("/")
        self._sender_email = sender_email or os.environ["MAILJET_SENDER_EMAIL"]
        self._sender_name = sender_name or os.environ.get("MAILJET_SENDER_NAME")

    def send_confirmation(self, request: ConfirmationEmailRequest) -> None:
        confirmation_link = (
            f"{self._public_frontend_base_url}/confirm?subscriptionId="
            f"{quote(request.subscription_id, safe='')}&token={quote(request.confirmation_token, safe='')}"
        )
        self._send_template(
            recipient_email=request.email,
            template_id=self._confirmation_template_id,
            variables={"confirmation_link": confirmation_link},
            custom_id=request.event_id,
            operation="send_confirmation",
        )

    def send_new_listings(self, notification: NewListingsNotification) -> None:
        unsubscribe_link = (
            f"{self._public_frontend_base_url}/unsubscribe?subscriptionId="
            f"{quote(notification.subscription_id, safe='')}&token={quote(notification.management_token, safe='')}"
        )
        self._send_template(
            recipient_email=notification.email,
            template_id=self._new_listings_template_id,
            variables={
                "subscription_id": notification.subscription_id,
                "management_token": notification.management_token,
                "unsubscribe_link": unsubscribe_link,
                "vehicle_name": notification.vehicle_name,
                "location": notification.location,
                "listing_count": len(notification.listings),
                "listings": [_listing_to_variables(item) for item in notification.listings],
            },
            custom_id=notification.event_id,
            operation="send_new_listings",
        )

    def _send_template(
        self,
        recipient_email: str,
        template_id: int,
        variables: dict[str, object],
        custom_id: str,
        operation: str,
    ) -> None:
        recipient: dict[str, str] = {"Email": recipient_email}
        sender: dict[str, str] = {"Email": self._sender_email}
        if self._sender_name:
            sender["Name"] = self._sender_name

        message: dict[str, object] = {
            "From": sender,
            "To": [recipient],
            "TemplateID": template_id,
            "TemplateLanguage": True,
            "Variables": variables,
        }
        if custom_id:
            message["CustomID"] = custom_id

        try:
            response = self._http_client.post(
                f"{self._base_url}/send",
                auth=(self._api_key, self._secret_key),
                headers={"accept": "application/json", "content-type": "application/json"},
                json={"Messages": [message]},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            provider_code, provider_message = _error_details(exc.response)
            raise EmailDeliveryError(
                "Email provider request failed",
                provider="mailjet",
                operation=operation,
                status_code=exc.response.status_code,
                provider_code=provider_code,
                provider_message=provider_message,
                retryable=exc.response.status_code == 429 or exc.response.status_code >= 500,
            ) from exc
        except httpx.HTTPError as exc:
            raise EmailDeliveryError(
                "Email provider request failed",
                provider="mailjet",
                operation=operation,
            ) from exc


class MailjetListingVariables(TypedDict):
    id: str
    title: str
    price: str
    manufacture_year: str
    model_year: str
    odometer: str | None
    transmission: str | None
    seller_city: str | None
    seller_state: str | None
    seller_type: str | None
    listing_url: str | None


def _listing_to_variables(item: ListingEmailItem) -> MailjetListingVariables:
    return {
        "id": item.listing_id,
        "title": item.title,
        "price": _format_brl(item.price),
        "manufacture_year": item.manufacture_year,
        "model_year": item.model_year,
        "odometer": f"{item.odometer:,}".replace(",", ".") if item.odometer is not None else None,
        "transmission": item.transmission,
        "seller_city": item.seller_city,
        "seller_state": item.seller_state,
        "seller_type": item.seller_type,
        "listing_url": item.listing_url,
    }


def _format_brl(price: float) -> str:
    formatted = f"{price:,.2f}"
    return f"R$ {formatted.replace(',', '_').replace('.', ',').replace('_', '.')}"


def _error_details(response: httpx.Response) -> tuple[str | None, str | None]:
    try:
        body = response.json()
    except ValueError:
        return None, None
    if not isinstance(body, dict):
        return None, None
    code = body.get("ErrorIdentifier") or body.get("ErrorCode")
    message = body.get("ErrorMessage") or body.get("ErrorInfo")
    return (
        str(code) if code is not None else None,
        str(message) if message is not None else None,
    )
