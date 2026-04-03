from __future__ import annotations

from datetime import datetime, timezone

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.geospatial import build_vector_tool_result, load_vector_input, write_vector_output
from tool_python_stubs.common.types import VectorToolResult


@tracked_tool
def coordinate_transform(
    in_features_resource_id: str | None = None,
    in_features_path: str | None = None,
    target_wkid: int = 4326,
) -> VectorToolResult:
    """Transform geometries or layers between coordinate reference systems.

    :param in_features_resource_id: Optional resource identifier of the input vector layer.
    :type in_features_resource_id: str | None
    :param in_features_path: Optional absolute path to the input vector layer.
    :type in_features_path: str | None
    :param target_wkid: EPSG or WKID code of the target CRS. Must be an integer greater than or equal to 1000.
    :type target_wkid: int
    :returns: A VectorAsset-compatible dictionary containing the reprojected layer and updated CRS metadata.
    :rtype: VectorToolResult
    """
    _gpd, gdf, lineage, error = load_vector_input(tool_name="coordinate_transform", resource_id=in_features_resource_id, file_path=in_features_path)
    if error:
        return error
    if target_wkid < 1000:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "target_wkid must be greater than or equal to 1000.",
        }
    try:
        from pyproj import CRS

        target_crs = CRS.from_epsg(target_wkid)
        transformed = gdf.to_crs(target_crs)
        file_path = write_vector_output(transformed, f"coordinate_transform_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}")
        return build_vector_tool_result(
            source_tool="coordinate_transform",
            gdf=transformed,
            file_path=file_path,
            lineage=lineage,
            extras={"out_coor_system": target_crs.name},
        )
    except Exception as exc:
        return {"outcome": "error", "error_code": "CRS_MISMATCH", "retryable": False, "recovery_hint": str(exc)}