from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListingSnapshot:
    """Represent the stable identity of a Webmotors listing."""

    listing_id: str
