"""Build canonical Webmotors URLs from a search-result record."""

import re
from collections.abc import Mapping
from typing import Any
from unicodedata import normalize


WEBMOTORS_PURCHASE_URL = "https://www.webmotors.com.br/comprar"


def build_listing_url(record: Mapping[str, Any]) -> str | None:
    """Return the Webmotors detail URL for a car search result.

    The Webmotors search API does not provide the card URL directly.  Its own
    ``createUrlAd`` logic derives it from the listing fields.  A malformed or
    incomplete result must not produce a guessed URL, so this function returns
    ``None`` in that case.
    """
    specification = record.get("Specification")
    if not isinstance(specification, Mapping):
        return None

    make = _nested_value(specification, "Make")
    model = _nested_value(specification, "Model")
    version = _nested_value(specification, "Version")
    doors = _integer_string(specification.get("NumberPorts"))
    manufacture_year = _integer_string(specification.get("YearFabrication"))
    model_year = _integer_string(specification.get("YearModel"))
    unique_id = _integer_string(record.get("UniqueId"))

    if (
        make is None
        or model is None
        or version is None
        or doors is None
        or manufacture_year is None
        or model_year is None
        or unique_id is None
    ):
        return None

    make_slug = _slugify(make)
    model_slug = _slugify(model)
    version_slug = _slugify(version)
    if not all((make_slug, model_slug, version_slug)):
        return None

    years = manufacture_year if manufacture_year == model_year else f"{manufacture_year}-{model_year}"
    return (
        f"{WEBMOTORS_PURCHASE_URL}/{make_slug}/{model_slug}/{version_slug}/"
        f"{doors}-portas/{years}/{unique_id}"
    )


def _nested_value(specification: Mapping[str, Any], key: str) -> str | None:
    value = specification.get(key)
    if not isinstance(value, Mapping):
        return None
    nested_value = value.get("Value")
    return nested_value.strip() if isinstance(nested_value, str) and nested_value.strip() else None


def _integer_string(value: Any) -> str | None:
    """Normalize API values such as ``2017``, ``2017.0`` and ``'2017.0'``."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer() or numeric < 0:
        return None
    return str(int(numeric))


def _slugify(value: str) -> str:
    """Mirror Webmotors cleanString options used for listing URL segments."""
    value = value.strip().lower().replace(".", "")
    ascii_value = normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
