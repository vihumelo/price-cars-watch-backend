from datetime import UTC, datetime
from dataclasses import replace

from services.monitoring.src.models.monitored_subscription import MonitoredSubscription
from services.monitoring.src.services.monitoring_service import MonitoringService


def test_run_updates_seen_ids_and_publishes_one_batch_per_subscription(
    subscription_reader, subscription_listings_updater, vehicle_listings_lookup,
    new_listings_publisher, monitored_subscription, current_listings,
):
    subscription_reader.list_active_subscriptions.return_value = [monitored_subscription]
    subscription_listings_updater.update_listings.return_value = True
    vehicle_listings_lookup.list_listings.return_value = current_listings
    service = MonitoringService(subscription_reader, subscription_listings_updater, vehicle_listings_lookup, new_listings_publisher)

    summary = service.run("run-123", checked_at=datetime(2026, 1, 3, tzinfo=UTC))

    assert summary == {"subscriptions_checked": 1, "listing_searches": 1, "new_listings_detected": 2, "notifications_published": 1}
    update = subscription_listings_updater.update_listings.call_args.args[0]
    assert update.seen_listing_ids == ("existing-1", "new-1", "new-2")
    event = new_listings_publisher.publish.call_args.args[0]
    assert [listing.listing_id for listing in event.listings] == ["new-1", "new-2"]


def test_run_updates_timestamp_without_publishing_when_all_listings_were_seen(
    subscription_reader, subscription_listings_updater, vehicle_listings_lookup,
    new_listings_publisher, monitored_subscription, current_listings,
):
    subscription_reader.list_active_subscriptions.return_value = [
        replace(monitored_subscription, seen_listing_ids=("existing-1", "new-1", "new-2"))
    ]
    subscription_listings_updater.update_listings.return_value = True
    vehicle_listings_lookup.list_listings.return_value = current_listings
    service = MonitoringService(subscription_reader, subscription_listings_updater, vehicle_listings_lookup, new_listings_publisher)

    summary = service.run("run-123")

    assert summary["new_listings_detected"] == 0
    subscription_listings_updater.update_listings.assert_called_once()
    new_listings_publisher.publish.assert_not_called()


def test_run_groups_equal_search_criteria_before_calling_vehicles(
    subscription_reader, subscription_listings_updater, vehicle_listings_lookup,
    new_listings_publisher, monitored_subscription, current_listings,
):
    second = replace(
        monitored_subscription,
        subscription_id="subscription-456",
        email="bia@example.com",
        management_token="second-token",
    )
    subscription_reader.list_active_subscriptions.return_value = [monitored_subscription, second]
    subscription_listings_updater.update_listings.return_value = True
    vehicle_listings_lookup.list_listings.return_value = current_listings
    service = MonitoringService(subscription_reader, subscription_listings_updater, vehicle_listings_lookup, new_listings_publisher)

    summary = service.run("run-123")

    assert summary["listing_searches"] == 1
    vehicle_listings_lookup.list_listings.assert_called_once()
    assert new_listings_publisher.publish.call_count == 2


def test_run_does_not_publish_if_subscription_was_cancelled_before_update(
    subscription_reader, subscription_listings_updater, vehicle_listings_lookup,
    new_listings_publisher, monitored_subscription, current_listings,
):
    subscription_reader.list_active_subscriptions.return_value = [monitored_subscription]
    subscription_listings_updater.update_listings.return_value = False
    vehicle_listings_lookup.list_listings.return_value = current_listings
    service = MonitoringService(subscription_reader, subscription_listings_updater, vehicle_listings_lookup, new_listings_publisher)

    summary = service.run("run-123")

    assert summary["new_listings_detected"] == 0
    new_listings_publisher.publish.assert_not_called()
