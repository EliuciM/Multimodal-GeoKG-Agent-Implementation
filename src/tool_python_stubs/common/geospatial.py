from __future__ import annotations

from pathlib import Path
from typing import Any

from .runtime import build_vector_result, dependency_error_result, ensure_output_dir, resolve_input_path


def require_geospatial_stack(tool_name: str):
    try:
        import geopandas as gpd
        from pyproj import CRS
    except ImportError:
        return None, None, dependency_error_result(["geopandas", "shapely", "pyproj"], tool_name)
    return gpd, CRS, None


def load_vector_input(
    *,
    tool_name: str,
    resource_id: str | None = None,
    file_path: str | None = None,
):
    gpd, _crs, error = require_geospatial_stack(tool_name)
    if error:
        return None, None, None, error
    try:
        resolved_path, lineage, _asset = resolve_input_path(resource_id=resource_id, file_path=file_path, expected_types=["vector_layer"])
    except ValueError as exc:
        return None, None, None, {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": str(exc),
        }
    gdf = gpd.read_file(resolved_path)
    return gpd, gdf, lineage, None


def metric_crs_for_gdf(gdf, CRS):
    if gdf.crs is None:
        raise ValueError("Input vector layer has no CRS defined.")
    gdf_wgs84 = gdf.to_crs("EPSG:4326") if str(gdf.crs) != "EPSG:4326" else gdf
    bounds = gdf_wgs84.total_bounds
    center_lon = float((bounds[0] + bounds[2]) / 2)
    center_lat = float((bounds[1] + bounds[3]) / 2)
    zone = int((center_lon + 180) / 6) + 1
    epsg = 32600 + zone if center_lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def write_vector_output(gdf, stem: str) -> str:
    file_path = ensure_output_dir("gis_output") / f"{stem}.geojson"
    gdf.to_file(file_path, driver="GeoJSON")
    return str(Path(file_path).resolve())


def vector_metadata(gdf) -> tuple[tuple[float, float, float, float], list[str], list[str], int]:
    if gdf.empty:
        return (0.0, 0.0, 0.0, 0.0), [], [column for column in gdf.columns if column != "geometry"], 0
    bounds = tuple(float(value) for value in gdf.total_bounds)
    geometry_types = sorted({str(value) for value in gdf.geometry.geom_type.dropna().tolist()})
    attribute_keys = [column for column in gdf.columns if column != "geometry"]
    return bounds, geometry_types, attribute_keys, int(len(gdf))


def build_vector_tool_result(*, source_tool: str, gdf, file_path: str, lineage: list[str] | None = None, extras: dict[str, Any] | None = None):
    bounds, geometry_types, attribute_keys, feature_count = vector_metadata(gdf)
    return build_vector_result(
        source_tool=source_tool,
        file_path=file_path,
        bounds=bounds,
        geometry_types=geometry_types,
        attribute_keys=attribute_keys,
        feature_count=feature_count,
        lineage=lineage,
        extras=extras,
    )