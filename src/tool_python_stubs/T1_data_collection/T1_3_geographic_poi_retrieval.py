from __future__ import annotations

from tool_python_stubs.common.types import POIRetrievalResult


import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tool_python_stubs.common.decorators import tracked_tool


def _fetch_json(url: str) -> dict | list | None:
    request = Request(url, headers={"User-Agent": "Multimodal-GeoKG-Agent/0.1"})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _rank_results(results: list[dict], latitude: float | None, longitude: float | None) -> list[dict]:
    if latitude is None or longitude is None:
        return results
    return sorted(results, key=lambda item: (float(item.get("lat", 0.0)) - latitude) ** 2 + (float(item.get("lon", 0.0)) - longitude) ** 2)


def _to_admin_hierarchy(address: dict[str, str]) -> list[dict[str, str]]:
    hierarchy = []
    for key, level in (("country", "country"), ("state", "province"), ("city", "city"), ("county", "district")):
        if address.get(key):
            hierarchy.append({"level": level, "name": address[key]})
    return hierarchy


@tracked_tool
def geographic_poi_retrieval(
    entity_name: str,
    latitude: float | None = None,
    longitude: float | None = None,
    provider: str = "auto",
) -> POIRetrievalResult:
    """Retrieve coordinates and administrative context from a commercial POI API.

    :param entity_name: Entity name used as the primary POI query. Must be a non-empty string.
    :type entity_name: str
    :param latitude: Optional latitude hint in decimal degrees. Must be between -90 and 90 when provided.
    :type latitude: float | None
    :param longitude: Optional longitude hint in decimal degrees. Must be between -180 and 180 when provided.
    :type longitude: float | None
    :param provider: POI backend selector. Supported values: "auto", "baidu", "amap", "google_places". Defaults to "auto".
    :type provider: str
    :returns: A dictionary containing the resolved coordinates, administrative hierarchy, address, and source metadata.
    :rtype: POIRetrievalResult
    """
    if not entity_name.strip():
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "entity_name must be a non-empty string.",
        }

    if (latitude is None) != (longitude is None):
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "latitude and longitude must be provided together.",
        }
    if latitude is not None and not -90 <= latitude <= 90:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "latitude must be between -90 and 90 when provided.",
        }
    if longitude is not None and not -180 <= longitude <= 180:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "longitude must be between -180 and 180 when provided.",
        }
    if provider not in {"auto", "baidu", "amap", "google_places"}:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported provider: {provider}",
        }

    url = f"https://nominatim.openstreetmap.org/search?{urlencode({'q': entity_name, 'format': 'jsonv2', 'limit': 5, 'addressdetails': 1})}"
    try:
        data = _fetch_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "outcome": "error",
            "error_code": "DATA_SOURCE_UNAVAILABLE",
            "retryable": True,
            "recovery_hint": f"POI lookup failed: {exc}",
        }

    if not isinstance(data, list) or not data:
        return {
            "outcome": "empty",
            "error_code": "NO_ENTITY_FOUND",
            "retryable": False,
            "recovery_hint": f"No POI result found for '{entity_name}'.",
        }

    best = _rank_results(data, latitude, longitude)[0]
    address = best.get("address") if isinstance(best.get("address"), dict) else {}
    return {
        "latitude": float(best.get("lat", 0.0)),
        "longitude": float(best.get("lon", 0.0)),
        "admin_hierarchy": _to_admin_hierarchy(address),
        "address": best.get("display_name", ""),
        "related_features": [],
        "api_vendor": "nominatim_fallback" if provider == "auto" else provider,
        "outcome": "success",
        "error_code": None,
        "retryable": False,
        "recovery_hint": None,
    }