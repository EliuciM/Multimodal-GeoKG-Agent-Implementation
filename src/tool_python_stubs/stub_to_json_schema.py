from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
TOOL_FILE_PATTERN = re.compile(r"^T\d+_\d+_.+\.py$")
TOOL_NAME_PATTERN = re.compile(r"^T\d+_\d+_(.+)$")
SCHEMA_DIRECTIVE_PATTERN = re.compile(r"^:schema\s+(?P<kind>\w+)(?:\s+(?P<name>[\w-]+))?:\s*(?P<value>.+)$")
PARAM_PATTERN = re.compile(r"^:param\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*):\s*(?P<value>.*)$")


@dataclass
class DocstringSchemaHints:
    strict: bool | None = None
    all_of: list[dict[str, Any]] = field(default_factory=list)
    any_of_groups: list[list[str]] = field(default_factory=list)
    one_of_groups: list[list[str]] = field(default_factory=list)
    dependent_required: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ParsedFunction:
    name: str
    description: str
    properties: dict[str, dict[str, Any]]
    required: list[str]
    hints: DocstringSchemaHints


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate function-style JSON tool schemas from Python tool contracts.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional file or directory paths. Relative paths are resolved from tool_python_stubs/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write one JSON file per tool contract under this directory. Defaults to stdout when omitted.",
    )
    parser.add_argument(
        "--strict-default",
        action="store_true",
        help="Set schema.strict=true unless overridden by a :schema strict: directive.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indent width for emitted JSON. Defaults to 2.",
    )
    return parser.parse_args()


def _resolve_input_paths(raw_paths: list[str]) -> list[Path]:
    if not raw_paths:
        return sorted(_iter_tool_files(PACKAGE_ROOT))

    resolved: list[Path] = []
    for raw_path in raw_paths:
        candidate = _resolve_candidate_path(raw_path)
        if candidate.is_dir():
            resolved.extend(sorted(_iter_tool_files(candidate)))
        elif candidate.is_file() and _is_tool_file(candidate):
            resolved.append(candidate)
        else:
            raise FileNotFoundError(f"Unsupported input path: {raw_path}")
    return _dedupe_paths(resolved)


def _resolve_candidate_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate

    candidates = [
        candidate,
        PACKAGE_ROOT / candidate,
        PACKAGE_ROOT.parent / candidate,
    ]
    for option in candidates:
        if option.exists():
            return option
    return PACKAGE_ROOT / candidate


def _iter_tool_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if _is_tool_file(path):
            files.append(path)
    return files


def _is_tool_file(path: Path) -> bool:
    if path.name in {"__init__.py", "stub_to_json_schema.py"}:
        return False
    if "common" in path.parts:
        return False
    return bool(TOOL_FILE_PATTERN.match(path.name))


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(resolved)
    return deduped


def _load_function_schema(source_path: Path) -> ParsedFunction:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    function_node = _find_target_function(tree, source_path)
    if function_node is None:
        raise ValueError(f"No public tool function found in {source_path}")

    description, param_docs, hints = _parse_docstring(ast.get_docstring(function_node) or "")
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []

    positional_args = [*function_node.args.posonlyargs, *function_node.args.args]
    positional_defaults = [None] * (len(positional_args) - len(function_node.args.defaults)) + list(function_node.args.defaults)
    for arg_node, default_node in zip(positional_args, positional_defaults):
        property_schema, is_required = _build_parameter_schema(arg_node, default_node, param_docs.get(arg_node.arg))
        properties[arg_node.arg] = property_schema
        if is_required:
            required.append(arg_node.arg)

    for arg_node, default_node in zip(function_node.args.kwonlyargs, function_node.args.kw_defaults):
        property_schema, is_required = _build_parameter_schema(arg_node, default_node, param_docs.get(arg_node.arg))
        properties[arg_node.arg] = property_schema
        if is_required:
            required.append(arg_node.arg)

    return ParsedFunction(
        name=function_node.name,
        description=description or _humanize_name(function_node.name),
        properties=properties,
        required=required,
        hints=hints,
    )


def _find_target_function(tree: ast.Module, source_path: Path) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    public_functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    ]
    if not public_functions:
        return None

    stem_match = TOOL_NAME_PATTERN.match(source_path.stem)
    expected_name = stem_match.group(1) if stem_match else None
    if expected_name:
        for node in public_functions:
            if node.name == expected_name:
                return node

    return public_functions[0]


def _parse_docstring(docstring: str) -> tuple[str, dict[str, str], DocstringSchemaHints]:
    lines = docstring.splitlines()
    summary = ""
    for line in lines:
        stripped = line.strip()
        if stripped:
            summary = stripped
            break

    param_docs: dict[str, str] = {}
    hints = DocstringSchemaHints()
    current_param: str | None = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            current_param = None
            continue

        param_match = PARAM_PATTERN.match(stripped)
        if param_match:
            current_param = param_match.group("name")
            param_docs[current_param] = param_match.group("value").strip()
            continue

        schema_match = SCHEMA_DIRECTIVE_PATTERN.match(stripped)
        if schema_match:
            _apply_schema_directive(hints, schema_match.group("kind"), schema_match.group("value"))
            current_param = None
            continue

        if current_param and not stripped.startswith(":"):
            param_docs[current_param] = f"{param_docs[current_param]} {stripped}".strip()

    return summary, param_docs, hints


def _apply_schema_directive(hints: DocstringSchemaHints, kind: str, value: str) -> None:
    normalized_kind = kind.strip().lower()
    if normalized_kind == "strict":
        hints.strict = value.strip().lower() in {"1", "true", "yes", "on"}
        return

    if normalized_kind in {"anyof", "oneof"}:
        names = [name.strip() for name in re.split(r"[,|]", value) if name.strip()]
        if names:
            if normalized_kind == "anyof":
                hints.any_of_groups.append(names)
            else:
                hints.one_of_groups.append(names)
        return

    if normalized_kind == "dependentrequired":
        for clause in value.split(";"):
            if "->" not in clause:
                continue
            source, targets = clause.split("->", 1)
            source_name = source.strip()
            target_names = [name.strip() for name in re.split(r"[,|]", targets) if name.strip()]
            if source_name and target_names:
                hints.dependent_required[source_name] = target_names


def _build_parameter_schema(
    arg_node: ast.arg,
    default_node: ast.expr | None,
    param_description: str | None,
) -> tuple[dict[str, Any], bool]:
    has_default = default_node is not None
    default_value = _literal_eval(default_node) if has_default else None
    annotation_schema = _annotation_to_schema(arg_node.annotation, unwrap_optional=has_default and default_value is None)
    property_schema = _merge_dicts(annotation_schema, _infer_constraints_from_description(param_description or ""))

    if param_description:
        property_schema["description"] = param_description
    if has_default and default_value is not None:
        property_schema["default"] = default_value

    return property_schema, not has_default


def _annotation_to_schema(annotation: ast.expr | None, unwrap_optional: bool = False) -> dict[str, Any]:
    if annotation is None:
        return {}

    union_members = _split_union(annotation)
    if len(union_members) > 1:
        non_null_members = [member for member in union_members if not _is_none_node(member)]
        has_null_member = len(non_null_members) != len(union_members)
        members_to_use = non_null_members if unwrap_optional and has_null_member else union_members
        rendered = [_annotation_to_schema(member, unwrap_optional=False) for member in members_to_use if not (_is_none_node(member) and unwrap_optional)]
        rendered = [schema for schema in rendered if schema]
        if len(rendered) == 1:
            if not unwrap_optional and has_null_member:
                return {"anyOf": [rendered[0], {"type": "null"}]}
            return rendered[0]
        if rendered:
            if not unwrap_optional and has_null_member:
                rendered.append({"type": "null"})
            return {"anyOf": rendered}
        return {}

    if _is_none_node(annotation):
        return {"type": "null"}

    if isinstance(annotation, ast.Name):
        return _name_to_schema(annotation.id)

    if isinstance(annotation, ast.Attribute):
        return _name_to_schema(annotation.attr)

    if isinstance(annotation, ast.Subscript):
        container_name = _annotation_name(annotation.value)
        if container_name in {"Annotated"}:
            annotated_args = _subscript_args(annotation)
            return _annotation_to_schema(annotated_args[0], unwrap_optional=unwrap_optional) if annotated_args else {}

        if container_name in {"Literal"}:
            literal_values = [_literal_eval(node) for node in _subscript_args(annotation)]
            literal_values = [value for value in literal_values if value is not None]
            schema: dict[str, Any] = {"enum": literal_values}
            json_type = _json_type_for_literals(literal_values)
            if json_type:
                schema["type"] = json_type
            return schema

        if container_name in {"list", "List", "Sequence", "Iterable"}:
            item_args = _subscript_args(annotation)
            items = _annotation_to_schema(item_args[0], unwrap_optional=False) if item_args else {}
            return {"type": "array", "items": items or {}}

        if container_name in {"dict", "Dict", "Mapping"}:
            dict_args = _subscript_args(annotation)
            if len(dict_args) == 2:
                value_schema = _annotation_to_schema(dict_args[1], unwrap_optional=False)
                return {"type": "object", "additionalProperties": value_schema or True}
            return {"type": "object"}

        if container_name in {"tuple", "Tuple"}:
            tuple_args = _subscript_args(annotation)
            if tuple_args and isinstance(tuple_args[-1], ast.Constant) and tuple_args[-1].value is Ellipsis:
                items = _annotation_to_schema(tuple_args[0], unwrap_optional=False)
                return {"type": "array", "items": items or {}}
            return {"type": "array", "prefixItems": [_annotation_to_schema(item, unwrap_optional=False) for item in tuple_args]}

    return {}


def _split_union(annotation: ast.expr) -> list[ast.expr]:
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return [*_split_union(annotation.left), *_split_union(annotation.right)]
    return [annotation]


def _is_none_node(node: ast.expr) -> bool:
    return (isinstance(node, ast.Constant) and node.value is None) or (isinstance(node, ast.Name) and node.id == "None")


def _annotation_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _subscript_args(node: ast.Subscript) -> list[ast.expr]:
    slice_node = node.slice
    if isinstance(slice_node, ast.Tuple):
        return list(slice_node.elts)
    return [slice_node]


def _name_to_schema(name: str) -> dict[str, Any]:
    mapping = {
        "str": {"type": "string"},
        "int": {"type": "integer"},
        "float": {"type": "number"},
        "bool": {"type": "boolean"},
        "dict": {"type": "object"},
        "list": {"type": "array", "items": {}},
        "Any": {},
        "None": {"type": "null"},
    }
    return dict(mapping.get(name, {}))


def _literal_eval(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _json_type_for_literals(values: list[Any]) -> str | None:
    if not values:
        return None
    if all(isinstance(value, bool) for value in values):
        return "boolean"
    if all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        return "integer"
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return "number"
    if all(isinstance(value, str) for value in values):
        return "string"
    return None


def _infer_constraints_from_description(description: str) -> dict[str, Any]:
    if not description:
        return {}

    lowered = description.lower()
    inferred: dict[str, Any] = {}

    if "non-empty string" in lowered:
        inferred["minLength"] = 1
    if "items must be unique" in lowered:
        inferred["uniqueItems"] = True
    if "at least one item" in lowered or "must contain at least one item" in lowered:
        inferred["minItems"] = 1

    enum_values = _extract_quoted_values(description)
    if enum_values and ("supported values" in lowered or "supported values per item" in lowered):
        inferred["enum"] = enum_values

    between_match = re.search(r"between\s+(-?\d+(?:\.\d+)?)\s+and\s+(-?\d+(?:\.\d+)?)", lowered)
    if between_match:
        minimum = _to_number(between_match.group(1))
        maximum = _to_number(between_match.group(2))
        if minimum is not None:
            inferred["minimum"] = minimum
        if maximum is not None:
            inferred["maximum"] = maximum

    minimum_patterns = [
        (r"greater than or equal to\s+(-?\d+(?:\.\d+)?)", "minimum"),
        (r"at least\s+(-?\d+(?:\.\d+)?)", "minimum"),
        (r"greater than\s+(-?\d+(?:\.\d+)?)", "exclusiveMinimum"),
    ]
    for pattern, key in minimum_patterns:
        match = re.search(pattern, lowered)
        if match:
            value = _to_number(match.group(1))
            if value is not None:
                inferred[key] = value
                break

    maximum_patterns = [
        (r"less than or equal to\s+(-?\d+(?:\.\d+)?)", "maximum"),
        (r"at most\s+(-?\d+(?:\.\d+)?)", "maximum"),
        (r"less than\s+(-?\d+(?:\.\d+)?)", "exclusiveMaximum"),
    ]
    for pattern, key in maximum_patterns:
        match = re.search(pattern, lowered)
        if match:
            value = _to_number(match.group(1))
            if value is not None:
                inferred[key] = value
                break

    return inferred


def _extract_quoted_values(text: str) -> list[str]:
    matches = re.findall(r'"([^"]+)"|\'([^\']+)\'|`([^`]+)`', text)
    values = [next(group for group in match if group) for match in matches]
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _to_number(raw_value: str) -> int | float | None:
    try:
        if "." in raw_value:
            return float(raw_value)
        return int(raw_value)
    except ValueError:
        return None


def _merge_dicts(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        elif key == "enum" and key in merged and isinstance(merged[key], list) and isinstance(value, list):
            merged[key] = list(dict.fromkeys([*merged[key], *value]))
        else:
            merged[key] = value
    return merged


def _humanize_name(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _build_tool_schema(parsed_function: ParsedFunction, strict_default: bool) -> dict[str, Any]:
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": parsed_function.properties,
        "required": parsed_function.required,
        "additionalProperties": False,
    }

    all_of = list(parsed_function.hints.all_of)
    for names in parsed_function.hints.any_of_groups:
        all_of.append({"anyOf": [{"required": [name]} for name in names]})
    for names in parsed_function.hints.one_of_groups:
        all_of.append({"oneOf": [{"required": [name]} for name in names]})
    if parsed_function.hints.dependent_required:
        parameters["dependentRequired"] = parsed_function.hints.dependent_required
    if all_of:
        parameters["allOf"] = all_of

    return {
        "type": "function",
        "name": parsed_function.name,
        "description": parsed_function.description,
        "parameters": parameters,
        "strict": parsed_function.hints.strict if parsed_function.hints.strict is not None else strict_default,
    }


def _write_schema_file(output_dir: Path, source_path: Path, schema: dict[str, Any], indent: int) -> Path:
    relative_path = source_path.relative_to(PACKAGE_ROOT)
    destination = output_dir / relative_path.with_suffix(".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(schema, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    return destination


def main() -> None:
    args = _parse_args()
    source_paths = _resolve_input_paths(args.paths)
    generated: dict[str, dict[str, Any]] = {}

    for source_path in source_paths:
        parsed_function = _load_function_schema(source_path)
        schema = _build_tool_schema(parsed_function, strict_default=args.strict_default)
        if args.output_dir is not None:
            _write_schema_file(args.output_dir, source_path, schema, indent=args.indent)
        else:
            generated[str(source_path.relative_to(PACKAGE_ROOT).with_suffix(".json"))] = schema

    if args.output_dir is None:
        print(json.dumps(generated, ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()