import json
from unittest.mock import Mock

from services.monitoring.src.models.new_listings_event import NewListingsEvent
from services.monitoring.src.providers.sqs_new_listings_publisher import SqsNewListingsPublisher


def test_publisher_enqueues_new_listings_event(monitored_subscription, current_listings):
    sqs_client = Mock()
    publisher = SqsNewListingsPublisher(
        "https://sqs.sa-east-1.amazonaws.com/123/new-listings",
        sqs_client,
    )
    event = NewListingsEvent(
        event_id="event-123",
        subscription_id=monitored_subscription.subscription_id,
        email=monitored_subscription.email,
        management_token=monitored_subscription.management_token,
        vehicle=monitored_subscription.vehicle,
        state=monitored_subscription.state,
        city=monitored_subscription.city,
        radius_km=monitored_subscription.radius_km,
        listings=(current_listings[1],),
    )

    publisher.publish(event)

    kwargs = sqs_client.send_message.call_args.kwargs
    assert kwargs["QueueUrl"] == "https://sqs.sa-east-1.amazonaws.com/123/new-listings"
    message = json.loads(kwargs["MessageBody"])
    assert message["eventId"] == "event-123"
    assert message["subscriptionId"] == "subscription-123"
    assert message["vehicle"]["make"] == "HONDA"
    assert "brand" not in message["vehicle"]
    assert message["listings"][0]["id"] == "new-1"
    assert message["listings"][0]["make"] == "HONDA"
    assert "brand" not in message["listings"][0]
    assert message["listings"][0]["listingUrl"].endswith("/new-1")
