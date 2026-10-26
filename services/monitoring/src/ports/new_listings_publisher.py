from typing import Protocol

from ..models.new_listings_event import NewListingsEvent


class NewListingsPublisher(Protocol):
    def publish(self, event: NewListingsEvent) -> None: ...
