from time import perf_counter
from typing import Any

from services.shared.api_gateway import is_non_empty_string, json_body, path_parameter, route_key
from services.shared.http import error_response, json_response
from services.shared.observability import (
    bind_context,
    clear_context,
    configure_logging,
    emit_metric,
    get_or_create_correlation_id,
    metrics,
)
from ..errors import VehicleNotFoundError, VehicleProviderUnavailableError
from ..models.vehicle import (
    Listing,
    ListingLocation,
    Make,
    VehicleModel,
    VehicleSelection,
    VehicleVersion,
    VehicleYear,
)
from ..providers.vehicle_provider_factory import build_vehicle_provider
from ..services.vehicle_service import VehicleService


service = VehicleService(build_vehicle_provider())
logger = configure_logging("vehicles")


@metrics.log_metrics
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    clear_context()
    bind_context(
        correlation_id=get_or_create_correlation_id(_correlation_id_from_event(event)),
        **_request_context(context),
    )

    try:
        event_route_key = route_key(event)

        if event_route_key == "GET /vehicles/makes":
            return list_makes_handler(event, context)
        if event_route_key == "GET /vehicles/makes/{makeId}/models":
            return list_models_handler(event, context)
        if event_route_key == "GET /vehicles/makes/{makeId}/models/{modelId}/versions":
            return list_versions_handler(event, context)
        if (
            event_route_key
            == "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years"
        ):
            return list_years_handler(event, context)
        if (
            event_route_key
            == "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years/{yearId}"
        ):
            return get_vehicle_handler(event, context)
        if event_route_key == "POST /internal/vehicles/listings":
            return list_listings_handler(event, context)

        logger.warning(
            "vehicle_request_rejected",
            operation="route_dispatch",
            route=event_route_key,
            status_code=404,
            reason="route_not_found",
        )
        return error_response(404, "ROUTE_NOT_FOUND", "Route not found")
    finally:
        clear_context()


def list_makes_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    started_at = perf_counter()
    logger.info("vehicle_request_started", operation="list_makes")
    try:
        makes = service.list_makes()
        emit_metric("VehicleQueries")
        logger.info(
            "vehicle_request_completed",
            operation="list_makes",
            status_code=200,
            count=len(makes),
            duration_ms=_duration_ms(started_at),
        )
        return json_response(200, [_make_to_dict(make) for make in makes])
    except VehicleProviderUnavailableError as exc:
        return _provider_unavailable_response("list_makes", started_at, exc)
    except Exception as exc:
        return _internal_error_response("list_makes", started_at, exc)


def list_models_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    make_id = path_parameter(event, "makeId")
    if make_id is None:
        return _invalid_request_response("list_models", "makeId")

    started_at = perf_counter()
    logger.info("vehicle_request_started", operation="list_models", make_id=make_id)
    try:
        models = service.list_models(make_id)
        emit_metric("VehicleQueries")
        logger.info(
            "vehicle_request_completed",
            operation="list_models",
            status_code=200,
            make_id=make_id,
            count=len(models),
            duration_ms=_duration_ms(started_at),
        )
        return json_response(200, [_model_to_dict(model) for model in models])
    except VehicleNotFoundError:
        return _not_found_response("list_models", started_at, make_id=make_id)
    except VehicleProviderUnavailableError as exc:
        return _provider_unavailable_response(
            "list_models", started_at, exc, make_id=make_id
        )
    except Exception as exc:
        return _internal_error_response("list_models", started_at, exc, make_id=make_id)


def list_versions_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    make_id = path_parameter(event, "makeId")
    model_id = path_parameter(event, "modelId")
    missing_parameter = "makeId" if make_id is None else "modelId" if model_id is None else None
    if missing_parameter is not None:
        return _invalid_request_response("list_versions", missing_parameter)

    assert make_id is not None
    assert model_id is not None

    started_at = perf_counter()
    logger.info(
        "vehicle_request_started",
        operation="list_versions",
        make_id=make_id,
        model_id=model_id,
    )
    try:
        versions = service.list_versions(make_id, model_id)
        emit_metric("VehicleQueries")
        logger.info(
            "vehicle_request_completed",
            operation="list_versions",
            status_code=200,
            make_id=make_id,
            model_id=model_id,
            count=len(versions),
            duration_ms=_duration_ms(started_at),
        )
        return json_response(200, [_version_to_dict(version) for version in versions])
    except VehicleNotFoundError:
        return _not_found_response(
            "list_versions", started_at, make_id=make_id, model_id=model_id
        )
    except VehicleProviderUnavailableError as exc:
        return _provider_unavailable_response(
            "list_versions", started_at, exc, make_id=make_id, model_id=model_id
        )
    except Exception as exc:
        return _internal_error_response(
            "list_versions", started_at, exc, make_id=make_id, model_id=model_id
        )


def list_years_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    make_id = path_parameter(event, "makeId")
    model_id = path_parameter(event, "modelId")
    version_id = path_parameter(event, "versionId")
    missing_parameter = next(
        (
            parameter
            for parameter, value in (
                ("makeId", make_id),
                ("modelId", model_id),
                ("versionId", version_id),
            )
            if value is None
        ),
        None,
    )
    if missing_parameter is not None:
        return _invalid_request_response("list_years", missing_parameter)

    assert make_id is not None
    assert model_id is not None
    assert version_id is not None

    started_at = perf_counter()
    logger.info(
        "vehicle_request_started",
        operation="list_years",
        make_id=make_id,
        model_id=model_id,
        version_id=version_id,
    )
    try:
        years = service.list_years(make_id, model_id, version_id)
        emit_metric("VehicleQueries")
        logger.info(
            "vehicle_request_completed",
            operation="list_years",
            status_code=200,
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
            count=len(years),
            duration_ms=_duration_ms(started_at),
        )
        return json_response(200, [_year_to_dict(year) for year in years])
    except VehicleNotFoundError:
        return _not_found_response(
            "list_years",
            started_at,
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
        )
    except VehicleProviderUnavailableError as exc:
        return _provider_unavailable_response(
            "list_years",
            started_at,
            exc,
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
        )
    except Exception as exc:
        return _internal_error_response(
            "list_years",
            started_at,
            exc,
            make_id=make_id,
            model_id=model_id,
            version_id=version_id,
        )


def get_vehicle_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    parameters = {
        "make_id": path_parameter(event, "makeId"),
        "model_id": path_parameter(event, "modelId"),
        "version_id": path_parameter(event, "versionId"),
        "year_id": path_parameter(event, "yearId"),
    }
    missing_parameter = next(
        (name for name, value in parameters.items() if value is None),
        None,
    )
    if missing_parameter is not None:
        return _invalid_request_response("get_vehicle", missing_parameter)

    make_id = parameters["make_id"]
    model_id = parameters["model_id"]
    version_id = parameters["version_id"]
    year_id = parameters["year_id"]
    assert make_id is not None
    assert model_id is not None
    assert version_id is not None
    assert year_id is not None

    started_at = perf_counter()
    logger.info("vehicle_request_started", operation="get_vehicle", **parameters)
    try:
        vehicle = service.get_vehicle(make_id, model_id, version_id, year_id)
        emit_metric("VehicleQueries")
        logger.info(
            "vehicle_request_completed",
            operation="get_vehicle",
            status_code=200,
            duration_ms=_duration_ms(started_at),
            **parameters,
        )
        return json_response(200, _vehicle_to_dict(vehicle))
    except VehicleNotFoundError:
        return _not_found_response("get_vehicle", started_at, **parameters)
    except VehicleProviderUnavailableError as exc:
        return _provider_unavailable_response("get_vehicle", started_at, exc, **parameters)
    except Exception as exc:
        return _internal_error_response("get_vehicle", started_at, exc, **parameters)


def list_listings_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    search = _parse_listing_search(event)
    if search is None:
        return _invalid_request_response("list_listings", "body")

    started_at = perf_counter()
    location = search.pop("location")
    logger.info("vehicle_request_started", operation="list_listings", **search)
    try:
        listings = service.list_listings(
            search["make_id"],
            search["model_id"],
            search["version_id"],
            search["year_id"],
            location,
        )
        emit_metric("VehicleQueries")
        logger.info(
            "vehicle_request_completed",
            operation="list_listings",
            status_code=200,
            count=len(listings),
            duration_ms=_duration_ms(started_at),
            **search,
        )
        return json_response(200, [_listing_to_dict(listing) for listing in listings])
    except VehicleNotFoundError:
        return _not_found_response("list_listings", started_at, **search)
    except VehicleProviderUnavailableError as exc:
        return _provider_unavailable_response("list_listings", started_at, exc, **search)
    except Exception as exc:
        return _internal_error_response("list_listings", started_at, exc, **search)


def _invalid_request_response(operation: str, parameter: str) -> dict[str, Any]:
    logger.warning(
        "vehicle_request_rejected",
        operation=operation,
        status_code=400,
        reason="missing_parameter",
        parameter=parameter,
    )
    return error_response(400, "INVALID_REQUEST", "Invalid request")


def _not_found_response(
    operation: str, started_at: float, **attributes: Any
) -> dict[str, Any]:
    logger.warning(
        "vehicle_not_found",
        operation=operation,
        status_code=404,
        duration_ms=_duration_ms(started_at),
        **attributes,
    )
    return error_response(404, "VEHICLE_NOT_FOUND", "Vehicle not found")


def _provider_unavailable_response(
    operation: str,
    started_at: float,
    error: VehicleProviderUnavailableError,
    **attributes: Any,
) -> dict[str, Any]:
    logger.warning(
        "vehicle_provider_unavailable",
        operation=operation,
        status_code=502,
        duration_ms=_duration_ms(started_at),
        provider=error.provider,
        provider_operation=error.operation,
        provider_status_code=error.status_code,
        provider_code=error.provider_code,
        provider_message=error.provider_message,
        retryable=error.retryable,
        error_message=str(error),
        **attributes,
    )
    return error_response(
        502,
        "VEHICLE_PROVIDER_UNAVAILABLE",
        "Vehicle provider is unavailable",
    )


def _internal_error_response(
    operation: str, started_at: float, exc: Exception, **attributes: Any
) -> dict[str, Any]:
    logger.exception(
        "vehicle_request_failed",
        operation=operation,
        status_code=500,
        duration_ms=_duration_ms(started_at),
        error_type=type(exc).__name__,
        **attributes,
    )
    return error_response(500, "INTERNAL_ERROR", "Internal server error")


def _make_to_dict(make: Make) -> dict[str, str]:
    return {"id": make.id, "name": make.name}


def _vehicle_to_dict(vehicle: VehicleSelection) -> dict[str, str]:
    return {
        "make": vehicle.make,
        "model": vehicle.model,
        "version": vehicle.version,
        "year": vehicle.year,
    }


def _model_to_dict(model: VehicleModel) -> dict[str, str]:
    return {"id": model.id, "name": model.name}


def _version_to_dict(version: VehicleVersion) -> dict[str, str]:
    return {"id": version.id, "name": version.name}


def _year_to_dict(year: VehicleYear) -> dict[str, str]:
    return {"id": year.id, "name": year.name}


def _listing_to_dict(listing: Listing) -> dict[str, str | int | float | bool | None]:
    return {
        "id": listing.id,
        "provider": listing.provider,
        "providerListingId": listing.provider_listing_id,
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


def _parse_listing_search(event: dict[str, Any]) -> dict[str, Any] | None:
    body = json_body(event)
    if not isinstance(body, dict):
        return None

    values = {
        "make_id": body.get("makeId"),
        "model_id": body.get("modelId"),
        "version_id": body.get("versionId"),
        "year_id": body.get("yearId"),
    }
    if not all(is_non_empty_string(value) for value in values.values()):
        return None

    city = body.get("city")
    state = body.get("state")
    postal_code = body.get("postalCode")
    for value in (city, state, postal_code):
        if value is not None and not is_non_empty_string(value):
            return None

    latitude = body.get("latitude")
    longitude = body.get("longitude")
    radius_km = body.get("radiusKm")
    numeric_values = (latitude, longitude, radius_km)
    if any(
        value is not None
        and (isinstance(value, bool) or not isinstance(value, (int, float)))
        for value in numeric_values
    ):
        return None

    if (latitude is None) != (longitude is None):
        return None
    if latitude is not None and not -90 <= float(latitude) <= 90:
        return None
    if longitude is not None and not -180 <= float(longitude) <= 180:
        return None
    if radius_km is not None and float(radius_km) < 0:
        return None
    if (latitude is not None or longitude is not None) and radius_km is None:
        return None

    location = ListingLocation(
        city=city,
        state=state,
        postal_code=postal_code,
        latitude=float(latitude) if latitude is not None else None,
        longitude=float(longitude) if longitude is not None else None,
        radius_km=float(radius_km) if radius_km is not None else None,
    )

    return {
        **{key: str(value) for key, value in values.items()},
        "location": location,
    }


def _duration_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 2)


def _correlation_id_from_event(event: dict[str, Any]) -> str | None:
    headers = event.get("headers")
    if not isinstance(headers, dict):
        return None

    for name, value in headers.items():
        if str(name).lower() == "x-correlation-id":
            return value if isinstance(value, str) else None
    return None


def _request_context(context: Any) -> dict[str, str]:
    request_id = getattr(context, "aws_request_id", None)
    return {"request_id": request_id} if isinstance(request_id, str) and request_id else {}
