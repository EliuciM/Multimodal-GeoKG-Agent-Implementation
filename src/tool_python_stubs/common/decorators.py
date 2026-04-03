from __future__ import annotations

import inspect
import time
from functools import wraps
from typing import Any, Callable

from .runtime import SessionManager


def tracked_tool(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Log tool calls and auto-register asset-producing results."""

    signature = inspect.signature(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        started = time.perf_counter()
        bound = signature.bind_partial(*args, **kwargs)
        result = func(*args, **kwargs)
        duration_ms = int((time.perf_counter() - started) * 1000)
        if isinstance(result, dict) and result.get("resource_id"):
            SessionManager().register_asset(result)
        SessionManager().log_call(func.__name__, dict(bound.arguments), result if isinstance(result, dict) else {"outcome": "error"}, duration_ms)
        return result

    return wrapper