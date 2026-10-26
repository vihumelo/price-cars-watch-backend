from datetime import UTC, datetime
from unittest.mock import ANY

from services.subscriptions.src.models.listing_snapshot import ListingSnapshot
from services.subscriptions.src.models.subscription import SubscriptionStatus
from services.subscriptions.src.models.subscription_listings_update import SubscriptionListingsUpdate
from services.subscriptions.src.services.confirm_subscription_service import ConfirmSubscriptionService
from services.subscriptions.src.services.create_subscription_service import CreateSubscriptionService
from services.subscriptions.src.services.list_monitoring_subscriptions_service import ListMonitoringSubscriptionsService
from services.subscriptions.src.services.update_subscription_listings_service import UpdateSubscriptionListingsService


def test_create_preserves_tokens_and_all_vehicle_criteria(repository, confirmation_publisher):
    repository.find_by_subscription_key.return_value = []
    service = CreateSubscriptionService(repository, confirmation_publisher)

    service.create_subscription(" Ana@Example.com ", "HONDA", "HR-V", "LX", "2017", "São Paulo", "Valinhos", -22.97056, -46.99583, 25)

    saved = repository.save.call_args.args[0]
    assert saved.email == "ana@example.com"
    assert saved.status == SubscriptionStatus.PENDING_CONFIRMATION
    assert saved.confirmation_token
    assert saved.management_token
    assert saved.subscription_key == "ana@example.com#HONDA#HR-V#LX#2017#São Paulo#Valinhos#-22.97056#-46.99583#25"
    confirmation_publisher.publish.assert_called_once_with(ANY)


def test_confirm_saves_every_current_listing_as_baseline(repository, listings_lookup, pending_subscription):
    repository.get_by_id.return_value = pending_subscription
    listings_lookup.list_listings.return_value = [ListingSnapshot("1"), ListingSnapshot("2"), ListingSnapshot("1")]
    service = ConfirmSubscriptionService(repository, listings_lookup)

    service.confirm_subscription("subscription-123", "confirm-token")

    persisted = repository.update.call_args.args[0]
    assert persisted.status == SubscriptionStatus.ACTIVE
    assert persisted.confirmation_token is None
    assert persisted.seen_listing_ids == ("1", "2")
    assert persisted.baseline_captured_at is not None


def test_update_seen_listings_only_for_active_subscription(repository, active_subscription):
    repository.get_by_id.return_value = active_subscription
    service = UpdateSubscriptionListingsService(repository)
    update = SubscriptionListingsUpdate("subscription-123", ("80851171", "81450964", "81450964"), datetime(2026, 1, 3, tzinfo=UTC))

    assert service.update_subscription_listings(update) is True
    persisted = repository.update.call_args.args[0]
    assert persisted.seen_listing_ids == ("80851171", "81450964")


def test_monitoring_exposes_criteria_and_seen_baseline(repository, active_subscription):
    repository.list_active.return_value = [active_subscription]

    result = ListMonitoringSubscriptionsService(repository).list_monitoring_subscriptions()

    assert result[0].city == "Valinhos"
    assert result[0].radius_km == 25
    assert result[0].seen_listing_ids == ("80851171",)
