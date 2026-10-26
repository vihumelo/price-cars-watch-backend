from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from services.subscriptions.src.models.subscription import Subscription, SubscriptionStatus, SubscriptionVehicle


@pytest.fixture
def repository() -> Mock:
    return Mock()


@pytest.fixture
def confirmation_publisher() -> Mock:
    return Mock()


@pytest.fixture
def listings_lookup() -> Mock:
    return Mock()


@pytest.fixture
def pending_subscription() -> Subscription:
    return Subscription(
        subscription_id="subscription-123",
        subscription_key="ana@example.com#HONDA#HR-V#LX#2017#São Paulo#Valinhos#-22.97056#-46.99583#25",
        email="ana@example.com", make_id="HONDA", model_id="HR-V", version_id="LX", year_id="2017",
        state="São Paulo", city="Valinhos", latitude=-22.97056, longitude=-46.99583, radius_km=25,
        status=SubscriptionStatus.PENDING_CONFIRMATION, management_token="manage-token",
        confirmation_token="confirm-token", created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def active_subscription(pending_subscription: Subscription) -> Subscription:
    return Subscription(
        subscription_id=pending_subscription.subscription_id, subscription_key=pending_subscription.subscription_key,
        email=pending_subscription.email, make_id=pending_subscription.make_id,
        model_id=pending_subscription.model_id, version_id=pending_subscription.version_id,
        year_id=pending_subscription.year_id, state=pending_subscription.state, city=pending_subscription.city,
        latitude=pending_subscription.latitude, longitude=pending_subscription.longitude,
        radius_km=pending_subscription.radius_km, status=SubscriptionStatus.ACTIVE,
        management_token=pending_subscription.management_token, created_at=pending_subscription.created_at,
        vehicle=SubscriptionVehicle("HONDA", "HR-V", "LX", "2017"),
        seen_listing_ids=("80851171",), confirmed_at=datetime(2026, 1, 2, tzinfo=UTC),
        baseline_captured_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
