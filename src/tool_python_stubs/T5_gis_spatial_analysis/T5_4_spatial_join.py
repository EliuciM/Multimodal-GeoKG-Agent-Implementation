from __future__ import annotations

from datetime import datetime, timezone

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.geospatial import build_vector_tool_result, load_vector_input, metric_crs_for_gdf, write_vector_output
from tool_python_stubs.common.types import VectorToolResult


@tracked_tool
def spatial_join(
    target_features_resource_id: str | None = None,
    target_features_path: str | None = None,
    join_features_resource_id: str | None = None,
    join_features_path: str | None = None,
    match_option: str = "INTERSECT",
    search_radius_meters: float | None = None,
) -> VectorToolResult:
    """Join attributes between spatial layers based on geometric relations.

    :param target_features_resource_id: Optional resource identifier of the target layer.
    :type target_features_resource_id: str | None
    :param target_features_path: Optional absolute path to the target layer.
    :type target_features_path: str | None
    :param join_features_resource_id: Optional resource identifier of the join layer.
    :type join_features_resource_id: str | None
    :param join_features_path: Optional absolute path to the join layer.
    :type join_features_path: str | None
    :param match_option: Spatial join rule. Supported values: "CLOSEST", "INTERSECT", "WITHIN", "CONTAINS", "WITHIN_A_DISTANCE".
    :type match_option: str
    :param search_radius_meters: Optional search radius in meters. Must be greater than 0 when provided.
    :type search_radius_meters: float | None
    :returns: A VectorAsset-compatible dictionary containing the joined layer and join quality statistics.
    :rtype: VectorToolResult
    """
    if match_option not in {"CLOSEST", "INTERSECT", "WITHIN", "CONTAINS", "WITHIN_A_DISTANCE"}:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported match_option: {match_option}",
        }

    gpd, target_gdf, target_lineage, error = load_vector_input(tool_name="spatial_join", resource_id=target_features_resource_id, file_path=target_features_path)
    if error:
        return error
    _gpd, join_gdf, join_lineage, error = load_vector_input(tool_name="spatial_join", resource_id=join_features_resource_id, file_path=join_features_path)
    if error:
        return error
    try:
        if target_gdf.crs != join_gdf.crs:
            join_gdf = join_gdf.to_crs(target_gdf.crs)

        if match_option == "CLOSEST":
            from pyproj import CRS

            metric_crs = metric_crs_for_gdf(target_gdf, CRS)
            result = gpd.sjoin_nearest(
                target_gdf.to_crs(metric_crs),
                join_gdf.to_crs(metric_crs),
                how="left",
                max_distance=search_radius_meters,
                distance_col="join_distance_m",
            ).to_crs(target_gdf.crs)
        else:
            if match_option == "WITHIN_A_DISTANCE":
                if not search_radius_meters or search_radius_meters <= 0:
                    return {"outcome": "error", "error_code": "INVALID_ARGUMENT", "retryable": False, "recovery_hint": "search_radius_meters is required for WITHIN_A_DISTANCE."}
                from pyproj import CRS

                metric_crs = metric_crs_for_gdf(join_gdf, CRS)
                buffered = join_gdf.to_crs(metric_crs)
                buffered.geometry = buffered.geometry.buffer(search_radius_meters)
                join_gdf = buffered.to_crs(target_gdf.crs)
                predicate = "intersects"
            else:
                predicate = {
                    "INTERSECT": "intersects",
                    "WITHIN": "within",
                    "CONTAINS": "contains",
                }.get(match_option, "intersects")
            result = gpd.sjoin(target_gdf, join_gdf, how="left", predicate=predicate)

        joined_count = int(result["index_right"].notna().sum()) if "index_right" in result.columns else int(len(result))
        unjoined_count = int(len(result) - joined_count)
        file_path = write_vector_output(result, f"spatial_join_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}")
        return build_vector_tool_result(
            source_tool="spatial_join",
            gdf=result,
            file_path=file_path,
            lineage=target_lineage + join_lineage,
            extras={"joined_count": joined_count, "unjoined_count": unjoined_count},
        )
    except Exception as exc:
        return {"outcome": "error", "error_code": "CRS_MISMATCH", "retryable": False, "recovery_hint": str(exc)}