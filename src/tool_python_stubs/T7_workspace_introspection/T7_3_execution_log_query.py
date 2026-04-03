from __future__ import annotations

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.runtime import SessionManager
from tool_python_stubs.common.types import ExecutionLogQueryResult


@tracked_tool
def execution_log_query(
    filter_tool: str | None = None,
    filter_status: str = "all",
    limit: int = 20,
) -> ExecutionLogQueryResult:
    """Query recent tool execution logs for the current session.

    :param filter_tool: Optional tool name used to filter the execution history.
    :type filter_tool: str | None
    :param filter_status: Outcome filter. Supported values: "success", "empty", "partial", "error", "all". Defaults to "all".
    :type filter_status: str
    :param limit: Maximum number of log entries to return. Must be an integer between 1 and 500. Defaults to 20.
    :type limit: int
    :returns: A dictionary containing matched execution log entries and summary metadata.
    :rtype: ExecutionLogQueryResult
    """
    if filter_status not in {"success", "empty", "partial", "error", "all"}:
        return {
            "entry_count": 0,
            "entries": [],
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": f"Unsupported filter_status: {filter_status}",
        }
    if not 1 <= limit <= 500:
        return {
            "entry_count": 0,
            "entries": [],
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "limit must be between 1 and 500.",
        }

    entries = SessionManager().get_call_log(filter_tool=filter_tool, filter_status=filter_status, limit=limit)
    return {
        "entry_count": len(entries),
        "entries": entries,
        "outcome": "success",
        "error_code": None,
        "retryable": False,
        "recovery_hint": None,
    }