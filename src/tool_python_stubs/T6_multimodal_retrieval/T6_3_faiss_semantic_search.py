from __future__ import annotations

from tool_python_stubs.common.types import SemanticSearchResult


def faiss_semantic_search(
    embedding_resource_id: str | None = None,
    embedding_file_path: str | None = None,
    top_k: int = 5,
    modalities: list[str] | None = None,
) -> SemanticSearchResult:
    """Search the multimodal FAISS index with an embedding query.

    :param embedding_resource_id: Optional resource identifier of the query embedding asset.
    :type embedding_resource_id: str | None
    :param embedding_file_path: Optional absolute path to the query embedding file.
    :type embedding_file_path: str | None
    :param top_k: Number of ranked matches to return. Must be an integer between 1 and 100. Defaults to 5.
    :type top_k: int
    :param modalities: Optional modality filter. Supported values per item: "raster", "vector", "text". Items must be unique when provided.
    :type modalities: list[str] | None
    :returns: A dictionary containing ranked entity matches, similarity scores, and optional asset metadata.
    :rtype: SemanticSearchResult
    """
    raise NotImplementedError("Stub only: implement embedding load, modality filtering, and ranked result assembly.")