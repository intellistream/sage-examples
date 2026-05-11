"""Static inspection helpers for example entry scripts."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import re

from .models import ArgumentDefinition


README_ENTRY_PATTERN = re.compile(r"^-\s+`(?P<script>run_[^`]+\.py)`\s+[—-]\s+(?P<description>.+)$")
ENV_LOOKUP_PATTERN = re.compile(
    r"(?:os\.environ\.get|os\.getenv)\(\s*[\"']([A-Z][A-Z0-9_]+)[\"']"
)
SECTION_HEADER_PATTERN = re.compile(r"^[A-Z][A-Za-z ]+:\s*$")


@dataclass(slots=True)
class ScriptInspection:
    description: str | None = None
    usage: str | None = None
    arguments: list[ArgumentDefinition] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    environment_variables: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    execution_mode: str = "cli"
    interactive: bool = False
    has_http: bool = False


def _literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


def _call_is_argument_parser(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr == "ArgumentParser"
    if isinstance(func, ast.Name):
        return func.id == "ArgumentParser"
    return False


def _find_argument_parser_calls(module: ast.Module) -> tuple[set[str], dict[str, object]]:
    parser_names: set[str] = set()
    parser_config: dict[str, object] = {}

    for node in ast.walk(module):
        call: ast.Call | None = None
        assigned_name: str | None = None
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_name = target.id
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and isinstance(node.value, ast.Call):
            call = node.value
            assigned_name = node.target.id
        elif isinstance(node, ast.Call):
            call = node

        if call is None or not _call_is_argument_parser(call):
            continue

        if assigned_name:
            parser_names.add(assigned_name)

        keywords = {keyword.arg: _literal(keyword.value) for keyword in call.keywords if keyword.arg}
        parser_config.setdefault("description", keywords.get("description"))
        parser_config.setdefault("epilog", keywords.get("epilog"))

    return parser_names, parser_config


def _resolve_kind(primary_name: str, action: str | None, type_name: str | None, help_text: str | None, choices: list[str]) -> str:
    lowered_name = primary_name.lower()
    lowered_help = (help_text or "").lower()
    if action in {"store_true", "store_false"}:
        return "flag"
    if choices:
        return "choice"
    if type_name in {"int", "float"}:
        return type_name
    if any(token in lowered_name for token in ["path", "file", "video", "config", "dataset", "output", "input"]):
        return "path"
    if any(token in lowered_help for token in ["path", "file", "directory", "dataset", "video", "config"]):
        return "path"
    return "string"


def _build_argument_definition(call: ast.Call) -> ArgumentDefinition | None:
    raw_names = []
    for argument in call.args:
        literal = _literal(argument)
        if isinstance(literal, str):
            raw_names.append(literal)

    if not raw_names:
        return None

    keywords = {keyword.arg: _literal(keyword.value) for keyword in call.keywords if keyword.arg}
    positional = all(not name.startswith("-") for name in raw_names)
    primary_name = next((name for name in raw_names if name.startswith("--")), raw_names[0])
    action = keywords.get("action") if isinstance(keywords.get("action"), str) else None
    help_text = keywords.get("help") if isinstance(keywords.get("help"), str) else None
    default_value = keywords.get("default")
    default_text = None if default_value is None else str(default_value)
    choices = [str(item) for item in keywords.get("choices", [])] if isinstance(keywords.get("choices"), (list, tuple, set)) else []
    type_name = keywords.get("type") if isinstance(keywords.get("type"), str) else None
    if type_name is None and isinstance(keywords.get("type"), type):
        type_name = keywords["type"].__name__

    required = bool(keywords.get("required", False))
    if positional:
        nargs = keywords.get("nargs")
        required = nargs not in {"?", "*"}

    value_name = keywords.get("metavar") if isinstance(keywords.get("metavar"), str) else None
    if value_name is None and action not in {"store_true", "store_false"}:
        value_name = primary_name.lstrip("-").replace("-", "_").upper()

    return ArgumentDefinition(
        names=raw_names,
        primary_name=primary_name,
        help=help_text,
        required=required,
        default=default_text,
        action=action,
        value_name=value_name,
        choices=choices,
        positional=positional,
        kind=_resolve_kind(primary_name, action, type_name, help_text, choices),
    )


def _extract_arguments(module: ast.Module, parser_names: set[str]) -> list[ArgumentDefinition]:
    arguments: list[ArgumentDefinition] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
            continue
        if parser_names and isinstance(node.func.value, ast.Name) and node.func.value.id not in parser_names:
            continue
        argument = _build_argument_definition(node)
        if argument is not None:
            arguments.append(argument)
    return sorted(arguments, key=lambda item: next((arg.lineno for arg in []), 0)) if False else arguments


def _extract_lines_from_section(text: str, header: str) -> list[str]:
    lines = text.splitlines()
    capture = False
    collected: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip()
        if line.strip() == header:
            capture = True
            continue
        if capture and not line.strip():
            continue
        if capture and SECTION_HEADER_PATTERN.match(line.strip()) and line.strip() != header:
            break
        if capture:
            stripped = line.strip()
            if stripped:
                collected.append(stripped)
    return collected


def _extract_examples(*texts: str) -> list[str]:
    examples: list[str] = []
    for text in texts:
        if not text:
            continue
        for line in _extract_lines_from_section(text, "Examples:"):
            if line.startswith("#"):
                continue
            examples.append(line)
    deduplicated = []
    seen = set()
    for example in examples:
        if example not in seen:
            seen.add(example)
            deduplicated.append(example)
    return deduplicated[:8]


def _extract_environment_variables(source: str, *texts: str) -> list[str]:
    variables = set(ENV_LOOKUP_PATTERN.findall(source))
    for text in texts:
        if not text:
            continue
        for line in _extract_lines_from_section(text, "Environment Variables:"):
            for candidate in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", line):
                variables.add(candidate)
    return sorted(variables)


def _detect_execution_mode(source: str, identifier: str, has_http: bool) -> tuple[str, bool]:
    if has_http:
        return "http", False
    if "ConsoleApp" in source or "interactive app" in source.lower():
        return "interactive", True
    if any(token in source for token in ["input_file", "output_file", "--input", "--output"]):
        return "batch", False
    if identifier.endswith("_alert") or identifier.endswith("_monitor"):
        return "stateful", False
    return "cli", False


def _detect_tags(identifier: str, source: str, has_http: bool, interactive: bool) -> list[str]:
    tags = []
    if has_http:
        tags.append("fastapi")
    if interactive:
        tags.append("interactive")
    llm_markers = ["llm", "prompt", "chat", "completion", "use_llm", "no-llm", "summar", "assistant", "coach", "qa"]
    if any(marker in source.lower() or marker in identifier.lower() for marker in llm_markers):
        tags.append("llm")
    if any(token in source for token in ["--json", "json_mode", "output-format json"]):
        tags.append("json")
    if any(token in source.lower() for token in ["dataset", "event-file", "csv", "video", "image"]):
        tags.append("filesystem")
    if identifier.endswith("_api"):
        tags.append("api")
    if not tags:
        tags.append("cli")
    return tags


@lru_cache(maxsize=1)
def load_readme_descriptions(root_dir: Path) -> dict[str, str]:
    readme_path = root_dir / "examples" / "README.md"
    if not readme_path.exists():
        return {}
    descriptions: dict[str, str] = {}
    for line in readme_path.read_text(encoding="utf-8").splitlines():
        match = README_ENTRY_PATTERN.match(line.strip())
        if not match:
            continue
        descriptions[match.group("script")] = match.group("description").strip().rstrip(".")
    return descriptions


def inspect_script(script_path: Path, *, description_override: str | None = None) -> ScriptInspection:
    source = script_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    docstring = ast.get_docstring(module) or ""
    parser_names, parser_config = _find_argument_parser_calls(module)
    arguments = _extract_arguments(module, parser_names)
    has_http = any(token in source for token in ["uvicorn.run", "create_fastapi_app", "FastAPI service"])
    identifier = script_path.stem.removeprefix("run_")
    execution_mode, interactive = _detect_execution_mode(source, identifier, has_http)
    description = description_override or parser_config.get("description") or docstring.splitlines()[0] if docstring else None
    usage_parts = [script_path.name]
    for argument in arguments:
        rendered = argument.primary_name if not argument.positional else argument.value_name or argument.primary_name
        if argument.action not in {"store_true", "store_false"} and not argument.positional:
            rendered = f"{rendered} {argument.value_name or 'VALUE'}"
        if not argument.required:
            rendered = f"[{rendered}]"
        usage_parts.append(rendered)
    usage = "python " + " ".join(usage_parts)
    examples = _extract_examples(docstring, str(parser_config.get("epilog") or ""))
    environment_variables = _extract_environment_variables(source, docstring, str(parser_config.get("epilog") or ""))
    tags = _detect_tags(identifier, source, has_http, interactive)
    return ScriptInspection(
        description=str(description) if description else None,
        usage=usage,
        arguments=arguments,
        examples=examples,
        environment_variables=environment_variables,
        tags=tags,
        execution_mode=execution_mode,
        interactive=interactive,
        has_http=has_http,
    )