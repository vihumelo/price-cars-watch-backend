from unittest.mock import Mock

import pytest

from services.vehicles.src.models.vehicle import (
    Listing,
    Make,
    VehicleModel,
    VehicleVersion,
    VehicleYear,
)


@pytest.fixture
def vehicle_provider() -> Mock:
    return Mock()


@pytest.fixture
def sample_make() -> Make:
    return Make(id="HONDA", name="HONDA")


@pytest.fixture
def sample_model() -> VehicleModel:
    return VehicleModel(id="CIVIC", name="CIVIC")


@pytest.fixture
def sample_version() -> VehicleVersion:
    return VehicleVersion(
        id="1.5 16V TURBO GASOLINA TOURING 4P CVT",
        name="1.5 16V TURBO GASOLINA TOURING 4P CVT",
    )


@pytest.fixture
def sample_year() -> VehicleYear:
    return VehicleYear(id="2020", name="2020")


@pytest.fixture
def sample_listing() -> Listing:
    return Listing(
        id="80947084",
        provider="webmotors",
        provider_listing_id="80947084",
        title="VOLKSWAGEN GOLF 1.6 MI SPORTLINE 8V FLEX 4P MANUAL",
        make="VOLKSWAGEN",
        model="GOLF",
        version="1.6 MI SPORTLINE 8V FLEX 4P MANUAL",
        manufacture_year="2008",
        model_year="2009",
        price=42000,
        odometer=177767,
        transmission="Manual",
        auction=False,
        armored="N",
        seller_city="Jacarezinho",
        seller_state="Paraná (PR)",
        seller_type="PJ",
        listing_url=(
            "https://www.webmotors.com.br/comprar/volkswagen/golf/"
            "16-mi-sportline-8v-flex-4p-manual/4-portas/2008-2009/80947084"
        ),
    )
