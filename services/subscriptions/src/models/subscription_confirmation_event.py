from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubscriptionConfirmationEvent:
    event_id: str
    subscription_id: str
    email: str
    confirmation_token: str
