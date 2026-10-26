from unittest.mock import Mock

import pytest

from services.monitoring.src.models.listing import Listing
from services.monitoring.src.models.monitored_subscription import MonitoredSubscription, MonitoredVehicle


@pytest.fixture
def subscription_reader() -> Mock:
    return Mock()


@pytest.fixture
def subscription_listings_updater() -> Mock:
    return Mock()


@pytest.fixture
def vehicle_listings_lookup() -> Mock:
    return Mock()


@pytest.fixture
def new_listings_publisher() -> Mock:
    return Mock()


@pytest.fixture
def monitored_subscription() -> MonitoredSubscription:
    return MonitoredSubscription(
        subscription_id="subscription-123", email="ana@example.com", management_token="manage-token",
        make_id="HONDA", model_id="HR-V", version_id="LX", year_id="2017",
        state="São Paulo", city="Valinhos", latitude=-22.97056, longitude=-46.99583,
        radius_km=25, vehicle=MonitoredVehicle("HONDA", "HR-V", "LX", "2017"),
        seen_listing_ids=("existing-1",),
    )


@pytest.fixture
def current_listings() -> list[Listing]:
    return [
        Listing("existing-1", "existing", "HONDA", "HR-V", "LX", "2017", "2017", 79000, None, None, False, None, "Valinhos", "SP", "PJ"),
        Listing("new-1", "new one", "HONDA", "HR-V", "LX", "2017", "2017", 80000, 50000, "Automática", False, "N", "Campinas", "SP", "PJ", "https://www.webmotors.com.br/comprar/honda/hr-v/lx/4-portas/2017/new-1"),
        Listing("new-2", "new two", "HONDA", "HR-V", "LX", "2017", "2017", 81000, None, None, False, None, "Campinas", "SP", "PJ"),
    ]
