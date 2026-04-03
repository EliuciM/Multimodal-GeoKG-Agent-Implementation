from __future__ import annotations

from tool_python_stubs.common.types import GraphToolResult


def graph_connection(
    vector_graph_resource_id: str | None = None,
    vector_graph_file_path: str | None = None,
    raster_graph_resource_id: str | None = None,
    raster_graph_file_path: str | None = None,
    text_graph_resource_id: str | None = None,
    text_graph_file_path: str | None = None,
    text_resource_id: str | None = None,
    text_file_path: str | None = None,
    spatial_threshold_meters: float = 300,
    semantic_threshold: float = 0.5,
) -> GraphToolResult:
    """Connect entities across modalities into unified graph relations.

    :param vector_graph_resource_id: Optional resource identifier of the vector graph asset.
    :type vector_graph_resource_id: str | None
    :param vector_graph_file_path: Optional absolute path to the vector graph file.
    :type vector_graph_file_path: str | None
    :param raster_graph_resource_id: Optional resource identifier of the raster graph asset.
    :type raster_graph_resource_id: str | None
    :param raster_graph_file_path: Optional absolute path to the raster graph file.
    :type raster_graph_file_path: str | None
    :param text_graph_resource_id: Optional resource identifier of a prebuilt text graph asset.
    :type text_graph_resource_id: str | None
    :param text_graph_file_path: Optional absolute path to a prebuilt text graph file.
    :type text_graph_file_path: str | None
    :param text_resource_id: Optional resource identifier of a raw text asset when no text graph is provided.
    :type text_resource_id: str | None
    :param text_file_path: Optional absolute path to a raw text file when no text graph is provided.
    :type text_file_path: str | None
    :param spatial_threshold_meters: Distance threshold for vector-raster linking in meters. Must be greater than 0. Defaults to 300.
    :type spatial_threshold_meters: float
    :param semantic_threshold: Similarity threshold for vector-text linking. Must be between 0 and 1 inclusive. Defaults to 0.5.
    :type semantic_threshold: float
    :returns: A GraphAsset-compatible dictionary containing the unified multimodal graph and cross-modal match statistics.
    :rtype: GraphToolResult
    """
    raise NotImplementedError("Stub only: implement graph loading, ID remapping, cross-modal linking, and quality evaluation.")