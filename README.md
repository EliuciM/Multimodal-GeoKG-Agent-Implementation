# Multimodal-GeoKG-Agent-Implementation

本仓库承载 `Multimodal-GeoKG-Agent` 的实现侧内容，围绕 companion specification repo 中定义的单一 MCP Server 工具合同落地 Python stub、共享类型和最小可运行实现。

## 仓库职责

- 对应 24 个 canonical tool contract 的 Python 模块。
- 共享资源对象、状态语义和本地运行时辅助代码。
- 后续 MCP server 打包、测试与真实执行逻辑。

## 目录结构

- `src/tool_python_stubs/`：与 specification 中 24 个工具合同一一对应的 Python 模块、共享类型和本地最小实现。

## 与规范仓库的关系

- 规范来源于 `Multimodal-GeoKG-Agent-Specification` 仓库。
- canonical MCP server 入口位于规范仓库的 `architecture/tool_mcp_server/README.md`。
- 每个工具的 source of truth 位于 `architecture/tool_mcp_server/` 下对应 Markdown 文件中的 Python Stub Block。
- 本仓库中的 `src/tool_python_stubs/` 负责把这些合同同步为可导入的 Python 接口，并为后续 schema 生成与实现开发提供基础。
- 同一工具在两个仓库中保持一致的工具编号，方便交叉检索与自动化同步。

## Schema 与打包

- `src/tool_python_stubs/stub_to_json_schema.py` 从函数签名和 docstring 中提取工具参数信息，生成函数式 JSON schema。
- 这些 schema 可作为后续单一 MCP server registry 的输入，而不是面向分散的独立 tool package。

## 运行时产物

- `tool_runtime_output/` 属于本地生成内容，不建议纳入版本管理。
- `__pycache__/`、虚拟环境和其他缓存目录默认忽略。
