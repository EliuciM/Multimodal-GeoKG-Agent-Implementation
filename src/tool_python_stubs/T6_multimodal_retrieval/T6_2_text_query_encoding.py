from __future__ import annotations

from tool_python_stubs.common.types import EmbeddingToolResult


def text_query_encoding(
    text: str | None = None,
    text_file_path: str | None = None,
    text_resource_id: str | None = None,
) -> EmbeddingToolResult:
    """Encode text queries into the shared embedding space.

    :param text: Optional raw text query. Must be a non-empty string when provided.
    :type text: str | None
    :param text_file_path: Optional absolute path to a plain-text query file.
    :type text_file_path: str | None
    :param text_resource_id: Optional resource identifier of a registered text asset.
    :type text_resource_id: str | None
    :returns: An EmbeddingAsset-compatible dictionary containing the encoded text embedding and embedding metadata.
    :rtype: EmbeddingToolResult
    """
    raise NotImplementedError("Stub only: implement source resolution, tokenizer/model dispatch, and embedding export.")