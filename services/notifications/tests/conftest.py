from unittest.mock import Mock

import pytest

from services.notifications.src.models.confirmation_email_request import ConfirmationEmailRequest
from services.notifications.src.models.new_listings_notification import ListingEmailItem, NewListingsNotification


@pytest.fixture
def email_provider() -> Mock:
    return Mock()


@pytest.fixture
def confirmation_request() -> ConfirmationEmailRequest:
    return ConfirmationEmailRequest("event-confirmation-123", "subscription-123", "ana@example.com", "confirm-token")


@pytest.fixture
def new_listings_notification() -> NewListingsNotification:
    return NewListingsNotification(
        event_id="event-listings-123", subscription_id="subscription-123", email="ana@example.com",
        management_token="manage-token", vehicle_name="HONDA HR-V LX 2017",
        location="Valinhos - São Paulo, raio de 25 km",
        listings=(ListingEmailItem("80851171", "HONDA HR-V LX", 79990, "2017", "2017", 50000, "Automática", "Campinas", "São Paulo (SP)", "PJ", "https://www.webmotors.com.br/comprar/honda/hr-v/lx/4-portas/2017/80851171"),),
    )
