# Python Tool Stubs

This package contains importable Python contracts aligned with the canonical MCP server specification in the companion `Multimodal-GeoKG-Agent-Specification` repository.

## Scope

- One Python module per tool.
- Shared resource objects and status semantics under `common/types.py`.
- Parseable function docstrings that mirror the latest Python Stub Block wording from `architecture/tool_mcp_server/`.
- Stub functions and minimal implementations that serve as interface contracts, IDE hints, JSON schema inputs, and implementation starting points.

## Suggested usage

```python
from tool_python_stubs.T1_data_collection.T1_1_satellite_image_download import satellite_image_download
from tool_python_stubs.common.types import RasterToolResult
```

## Generate JSON schema

You can generate function-style JSON tool schemas directly from the Python modules with:

```bash
python -m tool_python_stubs.stub_to_json_schema --output-dir generated_tool_schemas
```

The generator reads function signatures and parseable docstrings, then writes one `.json` file per tool while preserving the `T1_*` to `T7_*` directory layout.

These generated schemas are intended to feed a unified MCP server tool registry, while remaining compatible with function-style tool metadata consumers.