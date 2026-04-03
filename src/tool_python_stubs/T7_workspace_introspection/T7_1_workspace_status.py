from __future__ import annotations

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.runtime import SessionManager
from tool_python_stubs.common.types import WorkspaceStatusResult


@tracked_tool
def workspace_status(
    filter_type: str = "all",
    filter_tool: str | None = None,
    only_usable: bool = False,
) -> WorkspaceStatusResult:
    """List assets registered in the current task session.

    :param filter_type: Resource type filter. Supported values: "raster_image", "vector_layer", "graph_file", "text_document", "embedding_vector", "all". Defaults to "all".
    :type filter_type: str
    :param filter_tool: Optional producer tool name used to filter the asset list.
    :type filter_tool: str | None
    :param only_usable: Whether to return only assets marked as usable. Defaults to False.
    :type only_usable: bool
    :returns: A dictionary containing matching session assets and their summary metadata.
    :rtype: WorkspaceStatusResult
    """
    if filter_type not in {"raster_image", "vector_layer", "graph_file", "text_document", "embedding_vector", "all"}:
        return {
            "asset_count": 0,
            "assets": [],
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported filter_type: {filter_type}",
        }

    assets = SessionManager().get_assets(filter_type=filter_type, filter_tool=filter_tool, only_usable=only_usable)
    summaries = []
    for asset in assets:
        summaries.append(
            {
                "resource_id": asset.get("resource_id", ""),
                "resource_type": asset.get("resource_type", ""),
                "source_tool": asset.get("source_tool", ""),
                "created_at": asset.get("created_at", ""),
                "file_path": asset.get("file_path", ""),
                "usable": asset.get("quality_indicators", {}).get("usable", True)
                if isinstance(asset.get("quality_indicators"), dict)
                else True,
                "lineage": asset.get("lineage", []),
            }
        )
    return {
        "asset_count": len(summaries),
        "assets": summaries,
        "outcome": "success",
        "error_code": None,
        "retryable": False,
        "recovery_hint": None,
    }