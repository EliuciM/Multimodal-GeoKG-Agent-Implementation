from __future__ import annotations

from tool_python_stubs.common.types import EmbeddingToolResult


def image_query_encoding(
    image_resource_id: str | None = None,
    image_file_path: str | None = None,
    image_base64: str | None = None,
) -> EmbeddingToolResult:
    """Encode image queries into the shared embedding space.

    :param image_resource_id: Optional resource identifier of a registered image asset.
    :type image_resource_id: str | None
    :param image_file_path: Optional absolute path to an input image file.
    :type image_file_path: str | None
    :param image_base64: Optional base64-encoded image payload. Must be a non-empty string when provided.
    :type image_base64: str | None
    :returns: An EmbeddingAsset-compatible dictionary containing the encoded image embedding and embedding metadata.
    :rtype: EmbeddingToolResult
    """
    raise NotImplementedError("Stub only: implement input normalization, encoder dispatch, and embedding export.")