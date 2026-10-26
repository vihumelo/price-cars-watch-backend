import json
from typing import Any, cast

import boto3

from services.shared.observability import get_correlation_id

from ..models.subscription_confirmation_event import SubscriptionConfirmationEvent
from ..ports.confirmation_email_publisher import ConfirmationEmailPublisher


class SqsConfirmationEmailPublisher(ConfirmationEmailPublisher):
    """Publish confirmation requests to the FIFO queue consumed by notifications."""

    def __init__(self, queue_url: str, sqs_client: Any | None = None) -> None:
        self._queue_url = queue_url
        self._sqs_client = cast(Any, sqs_client or boto3.client("sqs"))

    def publish(self, event: SubscriptionConfirmationEvent) -> None:
        message: dict[str, str] = {
            "eventId": event.event_id,
            "subscriptionId": event.subscription_id,
            "email": event.email,
            "confirmationToken": event.confirmation_token,
        }
        correlation_id = get_correlation_id()
        if correlation_id:
            message["correlationId"] = correlation_id
        self._sqs_client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(message),
            MessageGroupId=event.subscription_id,
            MessageDeduplicationId=event.event_id,
        )
