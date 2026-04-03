from __future__ import annotations

from tool_python_stubs.common.types import VectorToolResult



import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.runtime import build_vector_result, write_json_output


def _post_form(url: str, data: dict[str, str]) -> dict | None:
    payload = urlencode(data).encode("utf-8")
    request = Request(url, data=payload, headers={"User-Agent": "Multimodal-GeoKG-Agent/0.1"})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _build_query(feature_name: str, around_point: dict[str, float] | None, area_name: str | None, feature_type: str) -> str:
    name_filter = f'[name="{feature_name}"]'
    type_filter = "" if feature_type == "auto" else f"[{feature_type}]"
    area_prefix = f'area[name="{area_name}"]->.searchArea;\n' if area_name else ""
    area_scope = "(area.searchArea)" if area_name else ""
    around_scope = (
        f'(around:{around_point["radius_meters"]},{around_point["latitude"]},{around_point["longitude"]})'
        if around_point
        else ""
    )
    return (
        "[out:json][timeout:120];\n"
        f"{area_prefix}"
        "(\n"
        f"  nwr{name_filter}{type_filter}{area_scope}{around_scope};\n"
        ");\n"
        "out geom tags;"
    )


def _geometry_from_element(element: dict) -> dict | None:
    if element.get("type") == "node":
        return {"type": "Point", "coordinates": [element.get("lon"), element.get("lat")]}
    geometry = element.get("geometry")
    if not isinstance(geometry, list) or len(geometry) < 2:
        return None
    coordinates = [[point["lon"], point["lat"]] for point in geometry if "lon" in point and "lat" in point]
    if len(coordinates) < 2:
        return None
    if coordinates[0] == coordinates[-1] and len(coordinates) >= 4:
        return {"type": "Polygon", "coordinates": [coordinates]}
    return {"type": "LineString", "coordinates": coordinates}


def _flatten_coordinates(geometry: dict) -> list[tuple[float, float]]:
    geometry_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if geometry_type == "Point":
        return [(float(coords[0]), float(coords[1]))]
    if geometry_type == "LineString":
        return [(float(x), float(y)) for x, y in coords]
    if geometry_type == "Polygon":
        return [(float(x), float(y)) for ring in coords for x, y in ring]
    return []


@tracked_tool
def osm_feature_retrieval(
    feature_name: str,
    around_point: dict[str, float] | None = None,
    area_name: str | None = None,
    feature_type: str = "auto",
) -> VectorToolResult:
    """Retrieve named OSM features with optional type and spatial filters.

    :param feature_name: Feature name matched against the OSM name tag. Must be a non-empty string.
    :type feature_name: str
    :param around_point: Optional circular search limiter with keys "latitude", "longitude", and "radius_meters". Latitude must be between -90 and 90, longitude between -180 and 180, and radius_meters must be greater than 0.
    :type around_point: dict[str, float] | None
    :param area_name: Optional named administrative area used to constrain the query.
    :type area_name: str | None
    :param feature_type: Optional primary OSM tag filter. Supported values: "waterway", "highway", "boundary", "landuse", "natural", "building", "auto".
    :type feature_type: str
    :returns: A VectorAsset-compatible dictionary containing matched OSM geometries and summary metadata.
    :rtype: VectorToolResult
    """
    if not feature_name.strip():
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "feature_name must be a non-empty string.",
        }

    allowed_feature_types = {"waterway", "highway", "boundary", "landuse", "natural", "building", "auto"}
    if feature_type not in allowed_feature_types:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported feature_type: {feature_type}",
        }

    if around_point is not None:
        if not isinstance(around_point, dict):
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "around_point must be an object with latitude, longitude, and radius_meters.",
            }
        required_keys = {"latitude", "longitude", "radius_meters"}
        if not required_keys.issubset(around_point):
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "around_point must include latitude, longitude, and radius_meters.",
            }
        try:
            around_point = {
                "latitude": float(around_point["latitude"]),
                "longitude": float(around_point["longitude"]),
                "radius_meters": float(around_point["radius_meters"]),
            }
        except (TypeError, ValueError):
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "around_point values must be numeric.",
            }
        if not -90 <= around_point["latitude"] <= 90:
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "around_point.latitude must be between -90 and 90.",
            }
        if not -180 <= around_point["longitude"] <= 180:
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "around_point.longitude must be between -180 and 180.",
            }
        if around_point["radius_meters"] <= 0:
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "around_point.radius_meters must be greater than 0.",
            }

    overpass_url = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    try:
        response = _post_form(overpass_url, {"data": _build_query(feature_name, around_point, area_name, feature_type)})
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "outcome": "error",
            "error_code": "DATA_SOURCE_UNAVAILABLE",
            "retryable": True,
            "recovery_hint": f"Overpass request failed: {exc}",
        }

    features = []
    geometry_types: set[str] = set()
    points: list[tuple[float, float]] = []
    for element in (response or {}).get("elements", []):
        geometry = _geometry_from_element(element)
        if geometry is None:
            continue
        geometry_types.add(geometry["type"])
        points.extend(_flatten_coordinates(geometry))
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {"osm_id": element.get("id"), "osm_type": element.get("type"), **(element.get("tags") or {})},
            }
        )

    if not features or not points:
        return {
            "outcome": "empty",
            "error_code": "NO_ENTITY_FOUND",
            "retryable": False,
            "recovery_hint": f"No OSM geometry found for '{feature_name}'.",
        }

    bounds = (
        min(point[0] for point in points),
        min(point[1] for point in points),
        max(point[0] for point in points),
        max(point[1] for point in points),
    )
    geojson = {"type": "FeatureCollection", "features": features}
    file_path = write_json_output("vectors", f"osm_{feature_name.replace(' ', '_')}", geojson)
    attribute_keys = sorted({key for feature in features for key in feature.get("properties", {}).keys()})
    return build_vector_result(
        source_tool="osm_feature_retrieval",
        file_path=file_path,
        bounds=bounds,
        geometry_types=sorted(geometry_types),
        attribute_keys=attribute_keys,
        feature_count=len(features),
    )