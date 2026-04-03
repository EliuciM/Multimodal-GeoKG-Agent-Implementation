from __future__ import annotations

from tool_python_stubs.common.types import QueryDraftResult


def query_generation(
    instruction: str,
    target_system: str = "auto",
    graph_resource_id: str | None = None,
    graph_file_path: str | None = None,
    allow_write_intent: bool = False,
) -> QueryDraftResult:
    """Generate Cypher or SQL queries without executing them.

    :param instruction: Natural-language instruction to translate into a database query. Must be a non-empty string.
    :type instruction: str
    :param target_system: Target backend selector. Supported values: "auto", "postgresql", "neo4j". Defaults to "auto".
    :type target_system: str
    :param graph_resource_id: Optional graph asset identifier used as retrieval context for query generation.
    :type graph_resource_id: str | None
    :param graph_file_path: Optional local graph file path used as retrieval context for query generation.
    :type graph_file_path: str | None
    :param allow_write_intent: Whether write-oriented instructions may be generated as write queries. Defaults to False.
    :type allow_write_intent: bool
    :returns: A dictionary containing the generated query, target database type, and review metadata.
    :rtype: QueryDraftResult
    """
    raise NotImplementedError("Stub only: implement schema-aware query generation and safety labeling.")