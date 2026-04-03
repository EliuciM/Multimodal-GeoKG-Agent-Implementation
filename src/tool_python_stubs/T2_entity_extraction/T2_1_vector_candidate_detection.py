from __future__ import annotations

from tool_python_stubs.common.types import VectorToolResult


def vector_candidate_detection(
    latitude: float,
    longitude: float,
    radius_meters: float,
    entity_type: str = "bridge",
) -> VectorToolResult:
    """Detect candidate infrastructure points from vector overlays.

    :param latitude: Latitude of the search center in decimal degrees. Must be between -90 and 90.
    :type latitude: float
    :param longitude: Longitude of the search center in decimal degrees. Must be between -180 and 180.
    :type longitude: float
    :param radius_meters: Search radius around the center point in meters. Must be greater than 0.
    :type radius_meters: float
    :param entity_type: Target infrastructure class. Supported values: "bridge", "tunnel", "overpass", "dam", "other". Defaults to "bridge".
    :type entity_type: str
    :returns: A VectorAsset-compatible dictionary containing detected candidate points and summary metadata.
    :rtype: VectorToolResult
    """
    raise NotImplementedError("Stub only: implement overlay strategy selection, candidate extraction, and deduplication.")