from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def get_workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_runtime_root() -> Path:
    runtime_root = get_workspace_root() / "tool_runtime_output"
    runtime_root.mkdir(parents=True, exist_ok=True)
    return runtime_root


def get_state_file() -> Path:
    return get_runtime_root() / "session_state.json"


def ensure_output_dir(name: str) -> Path:
    output_dir = get_runtime_root() / name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_resource_id(resource_type: str, source_tool: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{resource_type}:{source_tool}:{timestamp}"


def _default_state() -> dict[str, list[dict[str, Any]]]:
    return {"assets": [], "call_log": []}


def _asset_is_usable(asset: dict[str, Any]) -> bool:
    quality = asset.get("quality_indicators")
    if isinstance(quality, dict) and "usable" in quality:
        return bool(quality.get("usable"))
    return True


def _summarize_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            path = Path(value)
            if path.exists() or path.suffix:
                return path.name if path.name else value
        except OSError:
            return value
    if isinstance(value, dict):
        return {key: _summarize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_summarize_value(item) for item in value]
    return value


class SessionManager:
    _instance: "SessionManager | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "SessionManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._file_lock = threading.Lock()
        return cls._instance

    def _load_state(self) -> dict[str, list[dict[str, Any]]]:
        state_file = get_state_file()
        if not state_file.exists():
            return _default_state()
        with self._file_lock:
            try:
                return json.loads(state_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return _default_state()

    def _save_state(self, state: dict[str, list[dict[str, Any]]]) -> None:
        with self._file_lock:
            get_state_file().write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def register_asset(self, asset: dict[str, Any]) -> None:
        state = self._load_state()
        state["assets"] = [item for item in state["assets"] if item.get("resource_id") != asset.get("resource_id")]
        state["assets"].append(asset)
        self._save_state(state)

    def log_call(self, tool_name: str, params: dict[str, Any], result: dict[str, Any], duration_ms: int) -> None:
        state = self._load_state()
        state["call_log"].append(
            {
                "call_id": f"call_{len(state['call_log']) + 1:05d}",
                "tool_name": tool_name,
                "called_at": utc_now_iso(),
                "duration_ms": duration_ms,
                "input_summary": _summarize_value(params),
                "output_resource_ids": [result["resource_id"]] if result.get("resource_id") else [],
                "outcome": result.get("outcome", "error"),
                "error_code": result.get("error_code"),
            }
        )
        self._save_state(state)

    def get_assets(self, filter_type: str = "all", filter_tool: str | None = None, only_usable: bool = False) -> list[dict[str, Any]]:
        filtered = []
        for asset in self._load_state()["assets"]:
            if filter_type != "all" and asset.get("resource_type") != filter_type:
                continue
            if filter_tool and asset.get("source_tool") != filter_tool:
                continue
            if only_usable and not _asset_is_usable(asset):
                continue
            filtered.append(asset)
        return sorted(filtered, key=lambda item: item.get("created_at", ""), reverse=True)

    def get_call_log(self, filter_tool: str | None = None, filter_status: str = "all", limit: int = 20) -> list[dict[str, Any]]:
        filtered = []
        for entry in self._load_state()["call_log"]:
            if filter_tool and entry.get("tool_name") != filter_tool:
                continue
            if filter_status != "all" and entry.get("outcome") != filter_status:
                continue
            filtered.append(entry)
        return list(reversed(filtered))[:limit]

    def resolve_asset(self, resource_id: str, expected_types: Iterable[str] | None = None) -> dict[str, Any]:
        assets = list(reversed(self._load_state()["assets"]))
        for asset in assets:
            if asset.get("resource_id") != resource_id:
                continue
            if expected_types and asset.get("resource_type") not in set(expected_types):
                raise ValueError(f"Asset '{resource_id}' does not match expected resource types {list(expected_types)}.")
            return asset
        raise ValueError(f"Unknown resource_id: {resource_id}")


def resolve_input_path(
    resource_id: str | None = None,
    file_path: str | None = None,
    expected_types: Iterable[str] | None = None,
) -> tuple[Path, list[str], dict[str, Any] | None]:
    if resource_id:
        asset = SessionManager().resolve_asset(resource_id, expected_types=expected_types)
        return Path(asset["file_path"]).resolve(), [resource_id], asset
    if file_path:
        return Path(file_path).resolve(), [], None
    raise ValueError("Either resource_id or file_path must be provided.")


def dependency_error_result(packages: list[str], tool_name: str) -> dict[str, Any]:
    package_text = ", ".join(packages)
    return {
        "outcome": "error",
        "error_code": "DEPENDENCY_MISSING",
        "retryable": False,
        "recovery_hint": f"Install required packages for {tool_name}: {package_text}.",
        "warnings": [f"Missing optional dependency set: {package_text}"],
    }

def write_json_output(subdir: str, stem: str, payload: dict[str, Any]) -> str:
    output_dir = ensure_output_dir(subdir)
    file_path = output_dir / f"{stem}.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(file_path.resolve())

def infer_language(text: str) -> str:
    return "zh" if any("\u4e00" <= char <= "\u9fff" for char in text) else "en"

def build_text_result(
    *,
    source_tool: str,
    title: str,
    content: str,
    source_type: str,
    source_url: str,
    file_path: str,
    lineage: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "resource_id": make_resource_id("text_document", source_tool),
        "resource_type": "text_document",
        "source_tool": source_tool,
        "file_path": str(Path(file_path).resolve()),
        "created_at": utc_now_iso(),
        "lineage": lineage or [],
        "warnings": warnings or [],
        "text_summary": {
            "title": title,
            "language": infer_language(content),
            "char_count": len(content),
            "source_type": source_type,
            "source_url": source_url,
        },
        "content": content,
        "outcome": "success" if content else "empty",
        "error_code": None if content else "NO_ENTITY_FOUND",
        "retryable": False,
        "recovery_hint": None if content else "No textual content was extracted.",
    }

def build_vector_result(
    *,
    source_tool: str,
    file_path: str,
    bounds: tuple[float, float, float, float],
    geometry_types: list[str],
    attribute_keys: list[str],
    feature_count: int,
    lineage: list[str] | None = None,
    warnings: list[str] | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "resource_id": make_resource_id("vector_layer", source_tool),
        "resource_type": "vector_layer",
        "source_tool": source_tool,
        "file_path": str(Path(file_path).resolve()),
        "created_at": utc_now_iso(),
        "lineage": lineage or [],
        "warnings": warnings or [],
        "spatial_extent": {
            "west": bounds[0],
            "south": bounds[1],
            "east": bounds[2],
            "north": bounds[3],
            "crs": "EPSG:4326",
        },
        "feature_summary": {
            "feature_count": feature_count,
            "geometry_types": geometry_types,
            "attribute_keys": attribute_keys,
        },
        "outcome": "success" if feature_count > 0 else "empty",
        "error_code": None if feature_count > 0 else "NO_ENTITY_FOUND",
        "retryable": False,
        "recovery_hint": None if feature_count > 0 else "No vector features were produced.",
    }
    if extras:
        result.update(extras)
    return result
