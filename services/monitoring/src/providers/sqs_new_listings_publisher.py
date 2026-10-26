import json
from typing import Any, cast

import boto3

from services.shared.observability import get_correlation_id

from ..models.new_listings_event import NewListingsEvent
from ..ports.new_listings_publisher import NewListingsPublisher


class SqsNewListingsPublisher(NewListingsPublisher):
    """Publish new-listing batches to the SQS queue consumed by notifications."""

    def __init__(self, queue_url: str, sqs_client: Any | None = None) -> None:
        self._queue_url = queue_url
        self._sqs_client = cast(Any, sqs_client or boto3.client("sqs"))

    def publish(self, event: NewListingsEvent) -> None:
        message: dict[str, Any] = {
            "eventId": event.event_id,
            "subscriptionId": event.subscription_id,
            "email": event.email,
            "managementToken": event.management_token,
            "vehicle": {
                "make": event.vehicle.make,
                "model": event.vehicle.model,
                "version": event.vehicle.version,
                "year": event.vehicle.year,
            },
            "location": {
                "state": event.state,
                "city": event.city,
                "radiusKm": event.radius_km,
            },
            "listings": [_listing_to_dict(listing) for listing in event.listings],
        }
        correlation_id = get_correlation_id()
        if correlation_id:
            message["correlationId"] = correlation_id
        self._sqs_client.send_message(QueueUrl=self._queue_url, MessageBody=json.dumps(message))


def _listing_to_dict(listing: Any) -> dict[str, Any]:
    return {
        "id": listing.listing_id,
        "title": listing.title,
        "make": listing.make,
        "model": listing.model,
        "version": listing.version,
        "manufactureYear": listing.manufacture_year,
        "modelYear": listing.model_year,
        "price": listing.price,
        "odometer": listing.odometer,
        "transmission": listing.transmission,
        "auction": listing.auction,
        "armored": listing.armored,
        "sellerCity": listing.seller_city,
        "sellerState": listing.seller_state,
        "sellerType": listing.seller_type,
        "listingUrl": listing.listing_url,
    }
