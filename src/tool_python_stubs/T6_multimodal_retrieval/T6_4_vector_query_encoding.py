from __future__ import annotations

from tool_python_stubs.common.types import EmbeddingToolResult


def vector_query_encoding(
    vector_resource_id: str | None = None,
    vector_file_path: str | None = None,
) -> EmbeddingToolResult:
    """Encode vector or geometry-derived queries into the shared embedding space.

    :param vector_resource_id: Optional resource identifier of the input vector asset.
    :type vector_resource_id: str | None
    :param vector_file_path: Optional absolute path to the input vector file.
    :type vector_file_path: str | None
    :returns: An EmbeddingAsset-compatible dictionary containing the encoded vector embedding and embedding metadata.
    :rtype: EmbeddingToolResult
    """
    raise NotImplementedError("Stub only: implement neighbourhood graph construction and vector encoder dispatch.")