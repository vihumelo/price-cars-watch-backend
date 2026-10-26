import re
from typing import Any
from unicodedata import normalize
from urllib.parse import urlencode

import httpx

from services.shared.observability import configure_logging

from ...errors import VehicleNotFoundError, VehicleProviderUnavailableError
from ...models.vehicle import (
    Listing,
    ListingLocation,
    Make,
    VehicleModel,
    VehicleSelection,
    VehicleVersion,
    VehicleYear,
)
from ...ports.vehicle_provider import VehicleProvider
from .webmotors_listing_url_builder import build_listing_url


logger = configure_logging("vehicles")


class WebmotorsProvider(VehicleProvider):
    """Adapt Webmotors' vehicle search filters to the vehicle provider contract."""

    DEFAULT_TIMEOUT = 5.0
    DEFAULT_BASE_URL = "https://www.webmotors.com.br/api/search/car"
    SEARCH_BASE_URL = "https://www.webmotors.com.br/carros/estoque"
    FILTER_NAME = "Make"
    YEAR_FILTER_NAME = "YearModel"
    STATE_CODES = {
        "acre": "ac",
        "alagoas": "al",
        "amapa": "ap",
        "amazonas": "am",
        "bahia": "ba",
        "ceara": "ce",
        "distrito-federal": "df",
        "espirito-santo": "es",
        "goias": "go",
        "maranhao": "ma",
        "mato-grosso": "mt",
        "mato-grosso-do-sul": "ms",
        "minas-gerais": "mg",
        "para": "pa",
        "paraiba": "pb",
        "parana": "pr",
        "pernambuco": "pe",
        "piaui": "pi",
        "rio-de-janeiro": "rj",
        "rio-grande-do-norte": "rn",
        "rio-grande-do-sul": "rs",
        "rondonia": "ro",
        "roraima": "rr",
        "santa-catarina": "sc",
        "sao-paulo": "sp",
        "sergipe": "se",
        "tocantins": "to",
    }
    DEFAULT_HEADERS = {
        "accept": "application/json",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
        ),
    }

    def __init__(
        self,
        http_client: httpx.Client | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._http_client = http_client or httpx.Client(
            timeout=timeout or self.DEFAULT_TIMEOUT
        )
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def list_makes(self) -> list[Make]:
        filters = self._search_filters(operation="list_makes")
        makes = self._filter_items(filters, self.FILTER_NAME)
        return [Make(id=name, name=name) for name in self._item_names(makes)]

    def list_models(self, make_id: str) -> list[VehicleModel]:
        filters = self._search_filters(make_id=make_id, operation="list_models")
        make = self._find_item(self._filter_items(filters, self.FILTER_NAME), make_id)
        return [
            VehicleModel(id=name, name=name)
            for name in self._item_names(self._items(make))
        ]

    def list_versions(self, make_id: str, model_id: str) -> list[VehicleVersion]:
        filters = self._search_filters(
            make_id=make_id,
            model_id=model_id,
            operation="list_versions",
        )
        make = self._find_item(self._filter_items(filters, self.FILTER_NAME), make_id)
        model = self._find_item(self._items(make), model_id)
        return [
            VehicleVersion(id=name, name=name)
            for name in self._item_names(self._items(model))
        ]

    def list_years(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
    ) -> list[VehicleYear]:
        filters = self._search_filters(
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
            operation="list_years",
        )
        years = self._filter_items(filters, self.YEAR_FILTER_NAME)
        return [VehicleYear(id=name, name=name) for name in self._item_names(years)]

    def get_vehicle(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
        year_id: str,
    ) -> VehicleSelection:
        years = self.list_years(make_id, model_id, version_id)
        if year_id not in {year.id for year in years}:
            raise VehicleNotFoundError("Webmotors vehicle year not found")
        return VehicleSelection(
            make=make_id,
            model=model_id,
            version=version_id,
            year=year_id,
        )

    def list_listings(
        self,
        make_id: str,
        model_id: str,
        version_id: str,
        year_id: str,
        location: ListingLocation,
    ) -> list[Listing]:
        """Retrieve every result page for the exact Webmotors vehicle search."""
        first_page = self._search(
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
            year_id=year_id,
            location=location,
            operation="list_listings",
            page=1,
        )
        listings = self._listings_from_response(first_page)
        page_total = self._page_total(first_page)

        for page in range(2, page_total + 1):
            response = self._search(
                make_id=make_id,
                model_id=model_id,
                version_id=version_id,
                year_id=year_id,
                location=location,
                operation="list_listings",
                page=page,
            )
            listings.extend(self._listings_from_response(response))

        return listings

    def _search_filters(
        self,
        make_id: str | None = None,
        model_id: str | None = None,
        version_id: str | None = None,
        operation: str = "search_filters",
    ) -> list[dict[str, Any]]:
        data = self._search(
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
            operation=operation,
            page=1,
        )
        filters = data.get("Filters") if isinstance(data, dict) else None
        if not isinstance(filters, list):
            raise self._provider_unavailable(
                "Unexpected Webmotors filters response",
                operation=operation,
            )
        return filters

    def _search(
        self,
        make_id: str | None = None,
        model_id: str | None = None,
        version_id: str | None = None,
        year_id: str | None = None,
        location: ListingLocation | None = None,
        operation: str = "search",
        page: int = 1,
    ) -> Any:
        internal_params: dict[str, str] = {
            "tipoveiculo": "carros",
            "page": str(page),
        }
        if make_id is not None:
            internal_params["marca1"] = make_id
        if model_id is not None:
            internal_params["modelo1"] = model_id
        if version_id is not None:
            internal_params["versao1"] = version_id
        if year_id is not None:
            internal_params["anode"] = year_id
            internal_params["anoate"] = year_id

        search_base_url = self.SEARCH_BASE_URL
        if location is not None and any(
            value is not None
            for value in (
                location.state,
                location.city,
                location.postal_code,
                location.latitude,
                location.longitude,
                location.radius_km,
            )
        ):
            if location.state is None or location.city is None:
                raise VehicleNotFoundError("Incomplete Webmotors location")

            coordinates = (location.latitude, location.longitude, location.radius_km)
            if any(value is not None for value in coordinates) and any(
                value is None for value in coordinates
            ):
                raise VehicleNotFoundError("Incomplete Webmotors location")

            state_code = self._state_code(location.state)
            city_slug = self._slug(location.city)
            if not city_slug:
                raise VehicleNotFoundError("Invalid Webmotors city")
            search_base_url = f"https://www.webmotors.com.br/carros/{state_code}-{city_slug}"
            internal_params["estadocidade"] = f"{location.state}-{location.city}"
            if all(value is not None for value in coordinates):
                assert location.latitude is not None
                assert location.longitude is not None
                assert location.radius_km is not None
                internal_params["localizacao"] = (
                    f"{self._number_string(location.latitude)},"
                    f"{self._number_string(location.longitude)}"
                    f"x{self._number_string(location.radius_km)}km"
                )

        return self._get(
            {
                "url": f"{search_base_url}?{urlencode(internal_params)}",
                "displayPerPage": "47",
                "actualPage": str(page),
                "showMenu": "true",
                "showCount": "true",
                "showBreadCrumb": "true",
                "order": "1",
                "mediaZeroKm": "false",
            },
            operation=operation,
        )

    def _get(self, params: dict[str, str], *, operation: str) -> Any:
        try:
            response = self._http_client.get(
                self._base_url,
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            response = getattr(exc, "response", None)
            status_code = response.status_code if response is not None else None
            provider_message = response.text[:500] if response is not None else str(exc)
            logger.exception(
                "webmotors_request_failed",
                provider="webmotors",
                operation=operation,
                status_code=status_code,
                error_type=type(exc).__name__,
            )
            raise self._provider_unavailable(
                "Webmotors provider request failed",
                operation=operation,
                status_code=status_code,
                provider_message=provider_message,
                retryable=status_code is None or status_code >= 500,
            ) from exc
        except ValueError as exc:
            logger.exception(
                "webmotors_request_failed",
                provider="webmotors",
                operation=operation,
                error_type=type(exc).__name__,
            )
            raise self._provider_unavailable(
                "Invalid Webmotors provider response",
                operation=operation,
                provider_message=str(exc),
            ) from exc

    def _headers(self) -> dict[str, str]:
        """Build the browser-like headers required by the Webmotors API."""
        return dict(self.DEFAULT_HEADERS)

    def _page_total(self, response: Any) -> int:
        pagination = response.get("Pagination") if isinstance(response, dict) else None
        page_total_value: object = (
            pagination.get("PageTotal") if isinstance(pagination, dict) else None
        )
        if isinstance(page_total_value, bool) or page_total_value is None:
            raise self._provider_unavailable("Invalid Webmotors pagination", operation="pagination")
        if not isinstance(page_total_value, (int, float, str)):
            raise self._provider_unavailable("Invalid Webmotors pagination", operation="pagination")
        try:
            page_total = int(page_total_value)
        except (TypeError, ValueError) as exc:
            raise self._provider_unavailable(
                "Invalid Webmotors pagination", operation="pagination"
            ) from exc
        if page_total < 0:
            raise self._provider_unavailable("Invalid Webmotors pagination", operation="pagination")
        return page_total

    def _listings_from_response(self, response: Any) -> list[Listing]:
        records = response.get("SearchResults") if isinstance(response, dict) else None
        if not isinstance(records, list):
            raise self._provider_unavailable(
                "Invalid Webmotors listings response", operation="list_listings"
            )
        return [self._listing_from_record(record) for record in records]

    def _listing_from_record(self, record: Any) -> Listing:
        if not isinstance(record, dict):
            raise self._provider_unavailable(
                "Invalid Webmotors listing", operation="list_listings"
            )
        specification = self._object(record, "Specification")
        seller = self._object(record, "Seller")
        prices = self._object(record, "Prices")

        unique_id = self._required_value(record, "UniqueId")
        title = self._required_string(specification, "Title")
        make = self._required_string(self._object(specification, "Make"), "Value")
        model = self._required_string(self._object(specification, "Model"), "Value")
        version = self._required_string(self._object(specification, "Version"), "Value")
        manufacture_year = self._year_string(
            self._required_value(specification, "YearFabrication")
        )
        model_year = self._year_string(
            self._required_value(specification, "YearModel")
        )
        price = self._required_number(prices, "Price")

        return Listing(
            id=f"webmotors:{unique_id}",
            provider="webmotors",
            provider_listing_id=str(unique_id),
            title=title,
            make=make,
            model=model,
            version=version,
            manufacture_year=manufacture_year,
            model_year=model_year,
            price=price,
            odometer=self._optional_int(specification.get("Odometer")),
            transmission=self._optional_string(specification.get("Transmission")),
            auction=self._optional_bool(specification.get("Auction")),
            armored=self._optional_string(specification.get("Armored")),
            seller_city=self._optional_string(seller.get("City")),
            seller_state=self._optional_string(seller.get("State")),
            seller_type=self._optional_string(seller.get("SellerType")),
            listing_url=build_listing_url(record),
        )

    def _provider_unavailable(
        self,
        message: str,
        *,
        operation: str,
        status_code: int | None = None,
        provider_code: str | None = None,
        provider_message: str | None = None,
        retryable: bool = True,
    ) -> VehicleProviderUnavailableError:
        return VehicleProviderUnavailableError(
            message,
            provider="webmotors",
            operation=operation,
            status_code=status_code,
            provider_code=provider_code,
            provider_message=provider_message or message,
            retryable=retryable,
        )

    def _object(self, value: dict[str, Any], key: str) -> dict[str, Any]:
        child = value.get(key)
        if not isinstance(child, dict):
            raise self._provider_unavailable(
                "Invalid Webmotors listing", operation="list_listings"
            )
        return child

    def _required_value(self, value: dict[str, Any], key: str) -> Any:
        result = value.get(key)
        if result is None or isinstance(result, bool):
            raise self._provider_unavailable(
                "Invalid Webmotors listing", operation="list_listings"
            )
        return result

    def _required_string(self, value: dict[str, Any], key: str) -> str:
        result = value.get(key)
        if not isinstance(result, str) or not result:
            raise self._provider_unavailable(
                "Invalid Webmotors listing", operation="list_listings"
            )
        return result

    def _required_number(self, value: dict[str, Any], key: str) -> int | float:
        result = value.get(key)
        if isinstance(result, bool) or not isinstance(result, (int, float)):
            raise self._provider_unavailable(
                "Invalid Webmotors listing", operation="list_listings"
            )
        return result

    def _year_string(self, value: Any) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, str) and value.endswith(".0"):
            try:
                parsed = float(value)
            except ValueError:
                return value
            if parsed.is_integer():
                return str(int(parsed))
        return str(value)

    def _state_code(self, state: str) -> str:
        code = self.STATE_CODES.get(self._slug(state))
        if code is None:
            raise VehicleNotFoundError("Webmotors state not found")
        return code

    def _slug(self, value: str) -> str:
        ascii_value = normalize("NFKD", value).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")

    def _number_string(self, value: float) -> str:
        numeric_value = float(value)
        return str(int(numeric_value)) if numeric_value.is_integer() else str(value)

    def _optional_string(self, value: Any) -> str | None:
        return value if isinstance(value, str) else None

    def _optional_int(self, value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def _optional_bool(self, value: Any) -> bool | None:
        return value if isinstance(value, bool) else None

    def _filter_items(self, filters: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
        for filter_item in filters:
            if isinstance(filter_item, dict) and filter_item.get("name") == name:
                return self._items(filter_item)
        raise VehicleNotFoundError("Webmotors vehicle filter not found")

    def _find_item(self, items: list[dict[str, Any]], name: str) -> dict[str, Any]:
        for item in items:
            if item.get("name") == name:
                return item
        raise VehicleNotFoundError("Webmotors vehicle not found")

    def _item_names(self, items: list[dict[str, Any]]) -> list[str]:
        names: list[str] = []
        for item in items:
            name = item.get("name")
            if not isinstance(name, str) or not name:
                raise self._provider_unavailable(
                    "Invalid Webmotors vehicle item", operation="vehicle_catalog"
                )
            names.append(name)
        return names

    def _items(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        items = item.get("items")
        if not isinstance(items, list):
            raise VehicleNotFoundError("Webmotors vehicle not found")
        if not all(isinstance(child, dict) for child in items):
            raise self._provider_unavailable(
                "Invalid Webmotors vehicle items", operation="vehicle_catalog"
            )
        return items
