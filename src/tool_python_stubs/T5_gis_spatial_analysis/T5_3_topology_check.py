from __future__ import annotations

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.geospatial import load_vector_input
from tool_python_stubs.common.types import TopologyCheckResult


@tracked_tool
def topology_check(
    in_features_resource_id: str | None = None,
    in_features_path: str | None = None,
    reference_features_resource_id: str | None = None,
    reference_features_path: str | None = None,
    relationship: str = "INTERSECT",
) -> TopologyCheckResult:
    """Check whether two feature layers satisfy a topological relationship.

    :param in_features_resource_id: Optional resource identifier of the input feature layer.
    :type in_features_resource_id: str | None
    :param in_features_path: Optional absolute path to the input feature layer.
    :type in_features_path: str | None
    :param reference_features_resource_id: Optional resource identifier of the reference feature layer.
    :type reference_features_resource_id: str | None
    :param reference_features_path: Optional absolute path to the reference feature layer.
    :type reference_features_path: str | None
    :param relationship: Topological relationship to check. Supported values: "INTERSECT", "WITHIN", "CONTAINS", "CROSSES", "TOUCHES", "OVERLAPS".
    :type relationship: str
    :returns: A dictionary containing the topology test result, matched feature identifiers, and summary counts.
    :rtype: TopologyCheckResult
    """
    _gpd, input_gdf, _lineage_a, error = load_vector_input(tool_name="topology_check", resource_id=in_features_resource_id, file_path=in_features_path)
    if error:
        return error
    _gpd, ref_gdf, _lineage_b, error = load_vector_input(tool_name="topology_check", resource_id=reference_features_resource_id, file_path=reference_features_path)
    if error:
        return error
    try:
        if input_gdf.crs != ref_gdf.crs:
            ref_gdf = ref_gdf.to_crs(input_gdf.crs)
        predicate = relationship.lower()
        if predicate == "intersect":
            predicate = "intersects"
        if predicate not in {"intersects", "within", "contains", "crosses", "touches", "overlaps"}:
            return {"outcome": "error", "error_code": "INVALID_ARGUMENT", "retryable": False, "recovery_hint": f"Unsupported relationship: {relationship}"}
        ref_union = ref_gdf.geometry.union_all() if hasattr(ref_gdf.geometry, "union_all") else ref_gdf.geometry.unary_union
        matched = []
        for index, row in input_gdf.iterrows():
            geometry = row.geometry
            if getattr(geometry, predicate)(ref_union):
                matched.append(str(index))
        return {"has_match": bool(matched), "match_count": len(matched), "matched_feature_ids": matched, "outcome": "success", "error_code": None, "retryable": False, "recovery_hint": None}
    except Exception as exc:
        return {"outcome": "error", "error_code": "CRS_MISMATCH", "retryable": False, "recovery_hint": str(exc)}