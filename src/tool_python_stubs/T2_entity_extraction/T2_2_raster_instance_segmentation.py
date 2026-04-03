from __future__ import annotations

from tool_python_stubs.common.types import RasterToolResult


def raster_instance_segmentation(
    raster_resource_id: str | None = None,
    raster_file_path: str | None = None,
    target_class: str = "bridge",
) -> RasterToolResult:
    """Run instance segmentation on a georeferenced raster.

    :param raster_resource_id: Optional resource identifier of the input raster asset.
    :type raster_resource_id: str | None
    :param raster_file_path: Optional absolute file path of the input raster image.
    :type raster_file_path: str | None
    :param target_class: Target object class to segment. Supported values: "bridge", "building", "road", "other". Defaults to "bridge".
    :type target_class: str
    :returns: A RasterAsset-compatible dictionary containing the segmentation mask and per-instance summaries.
    :rtype: RasterToolResult
    """
    raise NotImplementedError("Stub only: implement resource resolution, model inference, and mask export.")