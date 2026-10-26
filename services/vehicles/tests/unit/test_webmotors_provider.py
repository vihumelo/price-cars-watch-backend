from unittest.mock import Mock

import pytest

from services.vehicles.src.errors import VehicleNotFoundError, VehicleProviderUnavailableError
from services.vehicles.src.providers.webmotors.webmotors_provider import WebmotorsProvider


def test_list_models_maps_absent_brand_to_not_found(monkeypatch):
    provider = WebmotorsProvider(base_url="https://webmotors.test/search")
    monkeypatch.setattr(
        provider,
        "_get",
        Mock(return_value={"Filters": [{"name": "Make", "items": []}]}),
    )

    with pytest.raises(VehicleNotFoundError):
        provider.list_models("HONDA")


def test_list_versions_rejects_invalid_nested_items(monkeypatch):
    provider = WebmotorsProvider(base_url="https://webmotors.test/search")
    monkeypatch.setattr(
        provider,
        "_get",
        Mock(
            return_value={
                "Filters": [{"name": "Make", "items": [{"name": "HONDA"}]}]
            }
        ),
    )

    with pytest.raises(VehicleNotFoundError):
        provider.list_versions("HONDA", "CIVIC")


def test_missing_year_filter_is_not_found(monkeypatch):
    provider = WebmotorsProvider(base_url="https://webmotors.test/search")
    monkeypatch.setattr(provider, "_get", Mock(return_value={"Filters": []}))

    with pytest.raises(VehicleNotFoundError):
        provider.list_years("HONDA", "CIVIC", "TOURING")


def test_malformed_filters_are_provider_unavailable(monkeypatch):
    provider = WebmotorsProvider(base_url="https://webmotors.test/search")
    monkeypatch.setattr(provider, "_get", Mock(return_value={"Filters": {}}))

    with pytest.raises(VehicleProviderUnavailableError):
        provider.list_makes()
