from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from ..models.subscription import Subscription, SubscriptionStatus
from ..models.subscription_confirmation_event import SubscriptionConfirmationEvent
from ..ports.confirmation_email_publisher import ConfirmationEmailPublisher
from ..ports.subscription_repository import SubscriptionRepository
from .tokens import generate_token


class CreateSubscriptionService:
    """Create or refresh Webmotors subscriptions while preserving FIPE token flow."""

    def __init__(self, repository: SubscriptionRepository, publisher: ConfirmationEmailPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    def create_subscription(self, email: str, make_id: str, model_id: str, version_id: str,
                            year_id: str, state: str, city: str, latitude: float,
                            longitude: float, radius_km: float) -> None:
        email = email.strip().lower()
        criteria = (make_id, model_id, version_id, year_id, state, city, latitude, longitude, radius_km)
        key = self._subscription_key(email, *criteria)
        existing = self._repository.find_by_subscription_key(key)
        if any(item.status == SubscriptionStatus.ACTIVE for item in existing):
            return
        pending = next((item for item in existing if item.status == SubscriptionStatus.PENDING_CONFIRMATION), None)
        if pending:
            refreshed = replace(pending, confirmation_token=generate_token())
            self._repository.update(refreshed)
            self._publish(refreshed)
            return
        subscription = Subscription(
            subscription_id=str(uuid4()), subscription_key=key, email=email,
            make_id=make_id, model_id=model_id, version_id=version_id, year_id=year_id,
            state=state, city=city, latitude=latitude, longitude=longitude, radius_km=radius_km,
            status=SubscriptionStatus.PENDING_CONFIRMATION,
            confirmation_token=generate_token(), management_token=generate_token(),
            created_at=datetime.now(UTC),
        )
        self._repository.save(subscription)
        self._publish(subscription)

    def _publish(self, subscription: Subscription) -> None:
        if not subscription.confirmation_token:
            raise ValueError("Confirmation token is required")
        self._publisher.publish(SubscriptionConfirmationEvent(
            event_id=str(uuid4()), subscription_id=subscription.subscription_id,
            email=subscription.email, confirmation_token=subscription.confirmation_token,
        ))

    @staticmethod
    def _subscription_key(email: str, make_id: str, model_id: str, version_id: str,
                          year_id: str, state: str, city: str, latitude: float,
                          longitude: float, radius_km: float) -> str:
        return "#".join(map(str, (email, make_id, model_id, version_id, year_id, state, city,
                                   latitude, longitude, radius_km)))
