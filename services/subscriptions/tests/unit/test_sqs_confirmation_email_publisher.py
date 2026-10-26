import json
from unittest.mock import Mock

from services.subscriptions.src.models.subscription_confirmation_event import (
    SubscriptionConfirmationEvent,
)
from services.subscriptions.src.providers.sqs_confirmation_email_publisher import (
    SqsConfirmationEmailPublisher,
)


def test_publisher_enqueues_confirmation_event_with_fifo_idempotency():
    sqs_client = Mock()
    publisher = SqsConfirmationEmailPublisher(
        "https://sqs.sa-east-1.amazonaws.com/123/confirmation.fifo",
        sqs_client,
    )

    publisher.publish(
        SubscriptionConfirmationEvent(
            event_id="event-123",
            subscription_id="subscription-123",
            email="ana@example.com",
            confirmation_token="confirmation-token",
        )
    )

    kwargs = sqs_client.send_message.call_args.kwargs
    assert kwargs["QueueUrl"] == "https://sqs.sa-east-1.amazonaws.com/123/confirmation.fifo"
    assert json.loads(kwargs["MessageBody"]) == {
        "eventId": "event-123",
        "subscriptionId": "subscription-123",
        "email": "ana@example.com",
        "confirmationToken": "confirmation-token",
    }
    assert kwargs["MessageGroupId"] == "subscription-123"
    assert kwargs["MessageDeduplicationId"] == "event-123"
