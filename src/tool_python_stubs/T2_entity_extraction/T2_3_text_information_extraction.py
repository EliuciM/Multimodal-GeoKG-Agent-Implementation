from __future__ import annotations

from tool_python_stubs.common.types import TextExtractionResult


def text_information_extraction(
    text: str | None = None,
    text_file_path: str | None = None,
    text_resource_id: str | None = None,
    entity_schema: list[str] | None = None,
    extraction_backend: str = "llm",
) -> TextExtractionResult:
    """Extract structured fields from a text source.

    :param text: Optional raw text input. Must be a non-empty string when provided.
    :type text: str | None
    :param text_file_path: Optional absolute path to a plain-text file.
    :type text_file_path: str | None
    :param text_resource_id: Optional resource identifier of a registered text asset.
    :type text_resource_id: str | None
    :param entity_schema: Optional field schema for extraction. Items must be unique strings and the list must contain at least one item when provided.
    :type entity_schema: list[str] | None
    :param extraction_backend: Extraction backend selector. Supported values: "llm", "openai", "regex". Defaults to "llm".
    :type extraction_backend: str
    :returns: A schema-aligned dictionary containing extracted fields and extraction metadata.
    :rtype: TextExtractionResult
    """
    raise NotImplementedError("Stub only: implement mutual-exclusion validation, extraction backend dispatch, and result shaping.")