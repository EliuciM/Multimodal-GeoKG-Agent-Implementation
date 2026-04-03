from __future__ import annotations

from datetime import datetime, timezone

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.geospatial import build_vector_tool_result, load_vector_input, metric_crs_for_gdf, write_vector_output
from tool_python_stubs.common.types import VectorToolResult


@tracked_tool
def buffer_analysis(
    in_features_resource_id: str | None = None,
    in_features_path: str | None = None,
    buffer_distance_meters: float = 1000,
) -> VectorToolResult:
    """Create buffer geometries around input features.

    :param in_features_resource_id: Optional resource identifier of the input vector layer.
    :type in_features_resource_id: str | None
    :param in_features_path: Optional absolute path to the input vector layer.
    :type in_features_path: str | None
    :param buffer_distance_meters: Buffer distance in meters. Must be greater than 0.
    :type buffer_distance_meters: float
    :returns: A VectorAsset-compatible dictionary containing the buffered geometry layer and summary metadata.
    :rtype: VectorToolResult
    """
    gpd, gdf, lineage, error = load_vector_input(tool_name="buffer_analysis", resource_id=in_features_resource_id, file_path=in_features_path)
    if error:
        return error
    if buffer_distance_meters <= 0:
        return {"outcome": "error", "error_code": "INVALID_ARGUMENT", "retryable": False, "recovery_hint": "buffer_distance_meters must be greater than zero."}
    try:
        from pyproj import CRS

        projected = gdf.to_crs(metric_crs_for_gdf(gdf, CRS))
        buffered = projected.copy()
        buffered.geometry = projected.geometry.buffer(buffer_distance_meters)
        output = buffered.to_crs(gdf.crs)
        file_path = write_vector_output(output, f"buffer_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}")
        return build_vector_tool_result(source_tool="buffer_analysis", gdf=output, file_path=file_path, lineage=lineage)
    except Exception as exc:
        return {"outcome": "error", "error_code": "CRS_MISMATCH", "retryable": False, "recovery_hint": str(exc)}