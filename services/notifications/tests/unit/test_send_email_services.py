from services.notifications.src.services.send_confirmation_email_service import SendConfirmationEmailService
from services.notifications.src.services.send_new_listings_email_service import SendNewListingsEmailService


def test_confirmation_delegates_request_to_provider(email_provider, confirmation_request):
    service = SendConfirmationEmailService(email_provider)

    service.send_confirmation_email(confirmation_request)

    email_provider.send_confirmation.assert_called_once_with(confirmation_request)


def test_new_listings_delegates_notification_to_provider(email_provider, new_listings_notification):
    service = SendNewListingsEmailService(email_provider)

    service.send_new_listings_email(new_listings_notification)

    email_provider.send_new_listings.assert_called_once_with(new_listings_notification)
