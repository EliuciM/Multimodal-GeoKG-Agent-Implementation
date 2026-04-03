from __future__ import annotations

from typing import Any, Literal, TypedDict

Outcome = Literal["success", "empty", "partial", "error"]
DBType = Literal["postgresql", "neo4j"]
ResourceType = Literal[
    "raster_image",
    "vector_layer",
    "graph_file",
    "text_document",
    "embedding_vector",
]


class SpatialExtent(TypedDict):
    west: float
    east: float
    south: float
    north: float
    crs: str


class RasterQualityIndicators(TypedDict, total=False):
    resolution_m: float
    width_px: int
    height_px: int
    usable: bool
    cloud_cover_pct: float | None


class FeatureSummary(TypedDict):
    feature_count: int
    geometry_types: list[str]
    attribute_keys: list[str]


class GraphSummary(TypedDict):
    node_count: int
    edge_count: int
    node_type_counts: dict[str, int]
    edge_type_counts: dict[str, int]


class GraphQualityIndicators(TypedDict, total=False):
    cross_modal_match_rate: float | None
    isolated_node_count: int


class TextSummary(TypedDict, total=False):
    title: str
    language: str
    char_count: int
    source_type: str
    source_url: str


class EmbeddingSummary(TypedDict):
    embedding_dim: int
    modality: Literal["raster", "vector", "text"]
    normalized: bool
    index_ready: bool


class ToolStatus(TypedDict, total=False):
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None
    warnings: list[str]


class BaseResource(TypedDict):
    resource_id: str
    resource_type: ResourceType
    source_tool: str
    file_path: str
    created_at: str
    lineage: list[str]
    warnings: list[str]


class RasterAsset(BaseResource):
    spatial_extent: SpatialExtent
    quality_indicators: RasterQualityIndicators


class VectorAsset(BaseResource):
    spatial_extent: SpatialExtent
    feature_summary: FeatureSummary


class GraphAsset(BaseResource):
    graph_summary: GraphSummary
    quality_indicators: GraphQualityIndicators


class TextAsset(BaseResource):
    text_summary: TextSummary


class EmbeddingAsset(BaseResource):
    embedding_summary: EmbeddingSummary


class RasterToolResult(RasterAsset, ToolStatus, total=False):
    pass


class VectorToolResult(VectorAsset, ToolStatus, total=False):
    pass


class GraphToolResult(GraphAsset, ToolStatus, total=False):
    pass


class TextToolResult(TextAsset, ToolStatus, total=False):
    content: str


class EmbeddingToolResult(EmbeddingAsset, ToolStatus, total=False):
    pass


class QueryDraftResult(TypedDict, total=False):
    query_id: str
    query: str
    db_type: DBType
    operation_type: Literal["read", "write"]
    requires_confirmation: bool
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class QueryExecutionResult(TypedDict, total=False):
    query_id: str
    db_type: DBType
    outcome: Outcome
    result: list[dict[str, Any]] | None
    affected_count: int | None
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class AdminUnit(TypedDict):
    level: str
    name: str


class RelatedFeature(TypedDict):
    feature_type: str
    name: str


class POIRetrievalResult(TypedDict, total=False):
    latitude: float
    longitude: float
    admin_hierarchy: list[AdminUnit]
    address: str
    related_features: list[RelatedFeature]
    api_vendor: str
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class TextExtractionResult(TypedDict, total=False):
    extracted_fields: dict[str, Any]
    filled_field_count: int
    missing_fields: list[str]
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class SearchMatch(TypedDict, total=False):
    entity_id: str
    similarity_score: float
    modality: Literal["raster", "vector", "text"]
    attributes: dict[str, Any]


class SemanticSearchResult(TypedDict, total=False):
    results: list[SearchMatch]
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class TopologyCheckResult(TypedDict, total=False):
    has_match: bool
    match_count: int
    matched_feature_ids: list[str]
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class WorkspaceAssetSummary(TypedDict, total=False):
    resource_id: str
    resource_type: ResourceType
    source_tool: str
    created_at: str
    file_path: str
    usable: bool
    lineage: list[str]


class WorkspaceStatusResult(TypedDict, total=False):
    asset_count: int
    assets: list[WorkspaceAssetSummary]
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class GraphHealthIndicators(TypedDict, total=False):
    cross_modal_match_rate: float | None
    isolated_node_fraction: float
    attribute_completeness: dict[str, float]


class GraphSummaryResult(TypedDict, total=False):
    node_count: int
    edge_count: int
    node_type_counts: dict[str, int]
    edge_type_counts: dict[str, int]
    health_indicators: GraphHealthIndicators
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None


class ExecutionLogEntry(TypedDict, total=False):
    call_id: str
    tool_name: str
    called_at: str
    duration_ms: int
    input_summary: dict[str, Any]
    output_resource_ids: list[str]
    outcome: Outcome
    error_code: str | None


class ExecutionLogQueryResult(TypedDict, total=False):
    entry_count: int
    entries: list[ExecutionLogEntry]
    outcome: Outcome
    error_code: str | None
    retryable: bool
    recovery_hint: str | None