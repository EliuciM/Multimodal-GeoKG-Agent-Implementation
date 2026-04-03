from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.runtime import SessionManager
from tool_python_stubs.common.types import GraphSummaryResult


@tracked_tool
def graph_summary(
    source: str = "neo4j",
    graph_resource_id: str | None = None,
    graph_file_path: str | None = None,
) -> GraphSummaryResult:
    """Summarize graph health metrics from a database or local graph asset.

    :param source: Graph source selector. Supported values: "neo4j", "local_asset", "local_file". Defaults to "neo4j".
    :type source: str
    :param graph_resource_id: Optional graph asset identifier used when source is "local_asset".
    :type graph_resource_id: str | None
    :param graph_file_path: Optional local graph file path used when source is "local_file".
    :type graph_file_path: str | None
    :returns: A dictionary containing graph health metrics, structural statistics, and optional quality indicators.
    :rtype: GraphSummaryResult
    """
    if source not in {"neo4j", "local_asset", "local_file"}:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported source: {source}",
        }

    if source == "neo4j":
        return {
            "outcome": "error",
            "error_code": "INDEX_NOT_FOUND",
            "retryable": False,
            "recovery_hint": "Live Neo4j querying is not configured in this minimal implementation yet.",
        }

    try:
        if source == "local_asset":
            if not graph_resource_id:
                raise ValueError("graph_resource_id is required when source='local_asset'.")
            asset = SessionManager().resolve_asset(graph_resource_id, expected_types=["graph_file"])
            path = Path(asset["file_path"]).resolve()
        else:
            if not graph_file_path:
                raise ValueError("graph_file_path is required when source='local_file'.")
            path = Path(graph_file_path).resolve()
    except ValueError as exc:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": str(exc),
        }

    if not path.exists():
        return {
            "outcome": "error",
            "error_code": "INDEX_NOT_FOUND",
            "retryable": False,
            "recovery_hint": f"Graph file not found: {path}",
        }

    graph = json.loads(path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_counts = Counter(node.get("type", "unknown") for node in nodes)
    edge_counts = Counter(edge.get("edge_type", "unknown") for edge in edges)
    connected = set()
    for edge in edges:
        connected.add(edge.get("source"))
        connected.add(edge.get("target"))
    isolated_count = sum(1 for node in nodes if node.get("id") not in connected)
    infrastructure_ids = {node.get("id") for node in nodes if node.get("type") in {"infrastructure", "bridge"}}
    cross_modal_ids = set()
    for edge in edges:
        if edge.get("edge_type") in {"vector_raster", "vector_text"}:
            cross_modal_ids.add(edge.get("source"))
            cross_modal_ids.add(edge.get("target"))
    match_rate = len(infrastructure_ids & cross_modal_ids) / len(infrastructure_ids) if infrastructure_ids else None
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(node_counts),
        "edge_type_counts": dict(edge_counts),
        "health_indicators": {
            "cross_modal_match_rate": match_rate,
            "isolated_node_fraction": isolated_count / len(nodes) if nodes else 0.0,
            "attribute_completeness": {},
        },
        "outcome": "success" if nodes else "empty",
        "error_code": None if nodes else "NO_ENTITY_FOUND",
        "retryable": False,
        "recovery_hint": None if nodes else "The graph file contains no nodes.",
    }