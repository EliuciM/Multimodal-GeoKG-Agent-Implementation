from __future__ import annotations

from tool_python_stubs.common.types import RasterToolResult


def satellite_image_download(
    latitude: float,
    longitude: float,
    zoom_level: int,
    radius_meters: float,
    provider: str = "google_satellite",
) -> RasterToolResult:
    """Download and mosaic satellite tiles around a center point.

    :param latitude: Latitude of the center point in decimal degrees. Must be between -90 and 90.
    :type latitude: float
    :param longitude: Longitude of the center point in decimal degrees. Must be between -180 and 180.
    :type longitude: float
    :param zoom_level: Tile zoom level. Must be an integer between 14 and 22.
    :type zoom_level: int
    :param radius_meters: Coverage radius around the center point in meters. Must be greater than 0.
    :type radius_meters: float
    :param provider: Satellite imagery provider. Supported values: "google_satellite", "bing_aerial", "mapbox_satellite", "gee". Defaults to "google_satellite".
    :type provider: str
    :returns: A RasterAsset-compatible dictionary describing the output GeoTIFF and its provenance metadata.
    :rtype: RasterToolResult
    """
    raise NotImplementedError("Stub only: implement tile fetch, mosaic, and GeoTIFF export.")