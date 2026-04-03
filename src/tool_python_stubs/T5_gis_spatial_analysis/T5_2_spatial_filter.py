from __future__ import annotations

from datetime import datetime, timezone

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.geospatial import build_vector_tool_result, load_vector_input, metric_crs_for_gdf, write_vector_output
from tool_python_stubs.common.types import VectorToolResult


@tracked_tool
def spatial_filter(
    in_features_resource_id: str | None = None,
    in_features_path: str | None = None,
    select_features_resource_id: str | None = None,
    select_features_path: str | None = None,
    overlap_type: str = "INTERSECT",
    search_distance_meters: float | None = None,
    where_clause: str | None = None,
) -> VectorToolResult:
    """Filter features by spatial relationship and optional attribute predicate.

    :param in_features_resource_id: Optional resource identifier of the input feature layer to be filtered.
    :type in_features_resource_id: str | None
    :param in_features_path: Optional absolute path to the input feature layer.
    :type in_features_path: str | None
    :param select_features_resource_id: Optional resource identifier of the spatial selector layer.
    :type select_features_resource_id: str | None
    :param select_features_path: Optional absolute path to the spatial selector layer.
    :type select_features_path: str | None
    :param overlap_type: Spatial relationship to evaluate. Supported values: "INTERSECT", "WITHIN", "CONTAINS", "WITHIN_A_DISTANCE", "HAVE_THEIR_CENTER_IN".
    :type overlap_type: str
    :param search_distance_meters: Optional search distance in meters. Must be greater than 0 when provided.
    :type search_distance_meters: float | None
    :param where_clause: Optional attribute predicate applied to the selected features.
    :type where_clause: str | None
    :returns: A VectorAsset-compatible dictionary containing the filtered feature layer and summary metadata.
    :rtype: VectorToolResult
    """
    if overlap_type not in {"INTERSECT", "WITHIN", "CONTAINS", "WITHIN_A_DISTANCE", "HAVE_THEIR_CENTER_IN"}:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported overlap_type: {overlap_type}",
        }

    gpd, input_gdf, input_lineage, error = load_vector_input(tool_name="spatial_filter", resource_id=in_features_resource_id, file_path=in_features_path)
    if error:
        return error
    _gpd, select_gdf, select_lineage, error = load_vector_input(tool_name="spatial_filter", resource_id=select_features_resource_id, file_path=select_features_path)
    if error:
        return error
    try:
        if input_gdf.crs != select_gdf.crs:
            select_gdf = select_gdf.to_crs(input_gdf.crs)

        if overlap_type == "WITHIN_A_DISTANCE":
            if not search_distance_meters or search_distance_meters <= 0:
                return {"outcome": "error", "error_code": "INVALID_ARGUMENT", "retryable": False, "recovery_hint": "search_distance_meters is required for WITHIN_A_DISTANCE."}
            from pyproj import CRS

            projected_crs = metric_crs_for_gdf(select_gdf, CRS)
            buffered = select_gdf.to_crs(projected_crs)
            buffered.geometry = buffered.geometry.buffer(search_distance_meters)
            select_gdf = buffered.to_crs(input_gdf.crs)
            predicate = "intersects"
            test_gdf = input_gdf
        elif overlap_type == "HAVE_THEIR_CENTER_IN":
            predicate = "within"
            test_gdf = input_gdf.copy()
            test_gdf.geometry = input_gdf.geometry.centroid
        else:
            predicate = {
                "INTERSECT": "intersects",
                "WITHIN": "within",
                "CONTAINS": "contains",
            }.get(overlap_type, "intersects")
            test_gdf = input_gdf

        selected = gpd.sjoin(test_gdf, select_gdf, how="inner", predicate=predicate)
        filtered = input_gdf.loc[selected.index.unique()].copy()
        if where_clause and not filtered.empty:
            filtered = filtered.query(where_clause)
        file_path = write_vector_output(filtered, f"spatial_filter_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}")
        return build_vector_tool_result(source_tool="spatial_filter", gdf=filtered, file_path=file_path, lineage=input_lineage + select_lineage, extras={"match_count": int(len(filtered))})
    except Exception as exc:
        return {"outcome": "error", "error_code": "CRS_MISMATCH", "retryable": False, "recovery_hint": str(exc)}