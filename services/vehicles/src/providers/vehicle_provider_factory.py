import os

from ..ports.vehicle_provider import VehicleProvider
from .webmotors.webmotors_provider import WebmotorsProvider


def build_vehicle_provider() -> VehicleProvider:
    provider_name = os.environ.get("VEHICLE_PROVIDER", "webmotors").strip().lower()

    if provider_name == "webmotors":
        return WebmotorsProvider()

    raise ValueError(f"Unsupported vehicle provider: {provider_name}")
