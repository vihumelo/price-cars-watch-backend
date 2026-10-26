from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from services.vehicles.src.errors import VehicleProviderUnavailableError
from services.vehicles.src.models.vehicle import ListingLocation
from services.vehicles.src.providers.webmotors.webmotors_provider import WebmotorsProvider


pytestmark = pytest.mark.integration


def test_provider_builds_nested_webmotors_search_url_and_maps_the_filter_tree():
    calls: list[dict[str, list[str]]] = []

    def request(request: httpx.Request) -> httpx.Response:
        outer_params = parse_qs(request.url.query.decode())
        internal_url = outer_params["url"][0]
        calls.append(parse_qs(urlparse(internal_url).query))
        return httpx.Response(
            200,
            json={
                "Filters": [
                    {
                        "name": "Make",
                        "items": [
                            {
                                "name": "HONDA",
                                "items": [
                                    {
                                        "name": "CIVIC",
                                        "items": [
                                            {
                                                "name": "TOURING",
                                                "selected": True,
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                    {"name": "YearModel", "items": [{"name": "2019"}, {"name": "2020"}]},
                ]
            },
        )

    provider = WebmotorsProvider(
        http_client=httpx.Client(transport=httpx.MockTransport(request)),
        base_url="https://webmotors.test/search",
    )

    assert [make.name for make in provider.list_makes()] == ["HONDA"]
    assert [model.name for model in provider.list_models("HONDA")] == ["CIVIC"]
    assert [version.name for version in provider.list_versions("HONDA", "CIVIC")] == ["TOURING"]
    assert [year.name for year in provider.list_years("HONDA", "CIVIC", "TOURING")] == ["2019", "2020"]
    assert calls[-1] == {
        "tipoveiculo": ["carros"],
        "page": ["1"],
        "marca1": ["HONDA"],
        "modelo1": ["CIVIC"],
        "versao1": ["TOURING"],
    }


def test_provider_http_error_becomes_provider_unavailable():
    provider = WebmotorsProvider(
        http_client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403))),
        base_url="https://webmotors.test/search",
    )

    with pytest.raises(VehicleProviderUnavailableError):
        provider.list_makes()


def test_list_listings_reads_all_pages_and_applies_geographic_filter():
    calls: list[tuple[str, str, str, str, str]] = []

    def request(request: httpx.Request) -> httpx.Response:
        outer_params = parse_qs(request.url.query.decode())
        internal_params = parse_qs(urlparse(outer_params["url"][0]).query)
        page = internal_params["page"][0]
        calls.append(
            (
                page,
                outer_params["actualPage"][0],
                urlparse(outer_params["url"][0]).path,
                internal_params["estadocidade"][0],
                internal_params["localizacao"][0],
            )
        )
        return httpx.Response(
            200,
            json={
                "SearchResults": [_listing_record(int(page))],
                "Pagination": {"PageCurrent": int(page), "PageTotal": 2},
            },
        )

    provider = WebmotorsProvider(
        http_client=httpx.Client(transport=httpx.MockTransport(request)),
        base_url="https://webmotors.test/search",
    )

    listings = provider.list_listings(
        "VOLKSWAGEN",
        "GOLF",
        "SPORTLINE",
        "2009",
        ListingLocation(
            state="São Paulo",
            city="Santo André",
            latitude=-23.66389,
            longitude=-46.53833,
            radius_km=25.0,
        ),
    )

    assert [listing.id for listing in listings] == ["webmotors:1001", "webmotors:1002"]
    assert listings[0].provider == "webmotors"
    assert listings[0].provider_listing_id == "1001"
    assert listings[0].make == "VOLKSWAGEN"
    assert listings[0].price == 42000
    assert listings[0].model_year == "2009"
    assert listings[0].seller_state == "Paraná (PR)"
    assert listings[0].listing_url == (
        "https://www.webmotors.com.br/comprar/volkswagen/golf/sportline/"
        "4-portas/2008-2009/1001"
    )
    assert calls == [
        (
            "1",
            "1",
            "/carros/sp-santo-andre",
            "São Paulo-Santo André",
            "-23.66389,-46.53833x25km",
        ),
        (
            "2",
            "2",
            "/carros/sp-santo-andre",
            "São Paulo-Santo André",
            "-23.66389,-46.53833x25km",
        ),
    ]


def test_list_listings_returns_empty_list_when_webmotors_has_no_results():
    provider = WebmotorsProvider(
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={"SearchResults": [], "Pagination": {"PageCurrent": 1, "PageTotal": 0}},
                )
            )
        ),
        base_url="https://webmotors.test/search",
    )

    assert provider.list_listings(
        "HONDA",
        "HR-V",
        "LX",
        "2017",
        ListingLocation(
            state="São Paulo",
            city="Santo André",
            latitude=-23.66389,
            longitude=-46.53833,
            radius_km=50,
        ),
    ) == []


def _listing_record(page: int) -> dict[str, object]:
    return {
        "UniqueId": 1000 + page,
        "Specification": {
            "Title": "VOLKSWAGEN GOLF 1.6 MI SPORTLINE 8V FLEX 4P MANUAL",
            "Make": {"Value": "VOLKSWAGEN"},
            "Model": {"Value": "GOLF"},
            "Version": {"Value": "SPORTLINE"},
            "NumberPorts": "4",
            "YearFabrication": "2008",
            "YearModel": "2009.0",
            "Odometer": 177767,
            "Transmission": "Manual",
            "Auction": False,
            "Armored": "N",
        },
        "Seller": {"City": "Jacarezinho", "State": "Paraná (PR)", "SellerType": "PJ"},
        "Prices": {"Price": 42000},
    }


def test_provider_sends_browser_headers_without_cookie_configuration():
    captured_headers: dict[str, str] = {}

    def request(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return httpx.Response(200, json={"Filters": [{"name": "Make", "items": []}]})

    provider = WebmotorsProvider(
        http_client=httpx.Client(transport=httpx.MockTransport(request)),
        base_url="https://webmotors.test/search",
    )

    assert provider.list_makes() == []
    assert captured_headers["accept"] == "application/json"
    assert captured_headers["accept-language"].startswith("pt-BR")
    assert captured_headers["sec-fetch-site"] == "same-origin"
    assert captured_headers["user-agent"].startswith("Mozilla/5.0")
    assert "cookie" not in captured_headers
