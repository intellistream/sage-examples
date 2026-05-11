"""Discovery helpers for SAGE example apps."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .default_inputs import apply_default_argument_values
from .introspection import inspect_script, load_readme_descriptions
from .models import (
    AppDefinition,
    DatasetConfig,
    FilesystemConfig,
    OpenAICompatibility,
    OpenAIRoutes,
    PortConfig,
    WebUIConfig,
)


def _titleize(identifier: str) -> str:
    return " ".join(part.capitalize() for part in identifier.split("_"))


def _description_from_identifier(identifier: str) -> str:
    if identifier.endswith("_api"):
        return f"{_titleize(identifier[:-4])} FastAPI service"
    return f"{_titleize(identifier)} CLI pipeline"


def _merge_override(base: AppDefinition, override: AppDefinition) -> AppDefinition:
    return AppDefinition(
        id=base.id,
        name=override.name or base.name,
        purpose=override.purpose or base.purpose,
        script_path=base.script_path,
        working_dir=base.working_dir,
        command=base.command,
        default_args=base.default_args,
        default_host=base.default_host,
        port=override.port,
        openai=override.openai,
        web_ui=override.web_ui,
        filesystem=override.filesystem,
        dataset=override.dataset,
        verified=override.verified,
        verification_status=override.verification_status,
        status_notes=override.status_notes,
        tags=sorted(set(base.tags + override.tags)),
        start_probe_path=override.start_probe_path,
        health_path=override.health_path,
        demo_run_path=override.demo_run_path,
        usage=base.usage,
        execution_mode=base.execution_mode,
        arguments=base.arguments,
        examples=base.examples,
        environment_variables=sorted(set(base.environment_variables + override.environment_variables)),
        launch_notes=base.launch_notes,
    )


def _infer_filesystem_notes(arguments: list) -> tuple[FilesystemConfig, DatasetConfig, list[str]]:
    path_arguments = [
        argument
        for argument in arguments
        if argument.kind == "path" or any(token in argument.primary_name for token in ["path", "file", "video", "config", "output", "input", "dataset"])
    ]
    dataset_arguments = [
        argument
        for argument in arguments
        if "dataset" in argument.primary_name or "event-file" in argument.primary_name or "model" in argument.primary_name
    ]
    notes: list[str] = []
    if path_arguments:
        notes.append(
            "Detected file/path args: " + ", ".join(argument.primary_name for argument in path_arguments[:6])
        )
    filesystem = FilesystemConfig(
        requires_workspace=bool(path_arguments),
        default_workspace=".sage" if path_arguments else None,
        notes=notes[0] if notes else None,
    )
    dataset = DatasetConfig(
        required=any(argument.required for argument in dataset_arguments),
        notes=(
            "Detected dataset or model related args: "
            + ", ".join(argument.primary_name for argument in dataset_arguments[:6])
        )
        if dataset_arguments
        else None,
    )
    return filesystem, dataset, notes


def _build_launch_notes(arguments: list, inspection) -> list[str]:
    notes: list[str] = []
    required_args = [argument.primary_name for argument in arguments if argument.required]
    if required_args:
        notes.append("Required args: " + ", ".join(required_args[:8]))
    if inspection.interactive:
        notes.append("Starts an interactive console flow unless you supply one-shot flags.")
    if inspection.environment_variables:
        notes.append("Environment variables: " + ", ".join(inspection.environment_variables[:8]))
    return notes


VERIFIED_APPS: dict[str, AppDefinition] = {
    "data_cleaner": AppDefinition(
        id="data_cleaner",
        name="Data Cleaner",
        purpose="CSV and tabular data cleaning demo.",
        script_path="examples/run_data_cleaner.py",
        working_dir=".",
        filesystem=FilesystemConfig(
            requires_workspace=True,
            default_workspace=".sage",
            notes="Verified with CSV input/output files managed outside source directories.",
        ),
        dataset=DatasetConfig(required=False, notes="No dataset registry required; user supplies input files."),
        verified=True,
        verification_status="verified",
        status_notes="Confirmed launch through OPC with required --input/--output args and JSON output artifact.",
        tags=["cli", "batch", "filesystem", "verified"],
    ),
    "ticket_triage_api": AppDefinition(
        id="ticket_triage_api",
        name="Ticket Triage API",
        purpose="Customer support ticket classification, urgency scoring, and queue routing.",
        script_path="examples/run_ticket_triage_api.py",
        working_dir=".",
        port=PortConfig(required=True, default=8010, configurable=True, arg="--port"),
        web_ui=WebUIConfig(
            starts_own_ui=True,
            url_template="http://127.0.0.1:{port}/dashboard/ui",
            open_path="/dashboard/ui",
        ),
        filesystem=FilesystemConfig(
            requires_workspace=True,
            default_workspace=".sage",
            outputs=".sage/opc-ticket-triage-state.json",
            notes="Optional JSON state file for persisted triage state.",
        ),
        dataset=DatasetConfig(required=False, notes="Uses bundled demo data via /demo/reset-and-run."),
        verified=True,
        verification_status="verified",
        status_notes="Confirmed launch with custom port and health/UI probes.",
        tags=["fastapi", "web-ui", "stateful", "verified"],
        start_probe_path="/",
        health_path="/health",
        demo_run_path="/demo/reset-and-run",
    ),
    "supply_chain_alert_api": AppDefinition(
        id="supply_chain_alert_api",
        name="Supply Chain Alert API",
        purpose="Supply risk dashboard and supplier alert service.",
        script_path="examples/run_supply_chain_alert_api.py",
        working_dir=".",
        port=PortConfig(required=True, default=8000, configurable=True, arg="--port"),
        web_ui=WebUIConfig(
            starts_own_ui=True,
            url_template="http://127.0.0.1:{port}/dashboard/ui",
            open_path="/dashboard/ui",
        ),
        filesystem=FilesystemConfig(
            requires_workspace=True,
            default_workspace=".sage",
            outputs=".sage/opc-supply-chain-alert-state.json",
            notes="Optional JSON state file for persisted supply chain state.",
        ),
        dataset=DatasetConfig(required=False, notes="Uses bundled demo events via /demo/reset-and-run."),
        verified=True,
        verification_status="verified",
        status_notes="Confirmed launch with allocated port plus health and dashboard UI probes.",
        tags=["fastapi", "web-ui", "stateful", "verified"],
        start_probe_path="/",
        health_path="/health",
        demo_run_path="/demo/reset-and-run",
    ),
}


def _build_generic_definition(script_path: Path) -> AppDefinition:
    identifier = script_path.stem.removeprefix("run_")
    readme_descriptions = load_readme_descriptions(script_path.parents[1])
    inspection = inspect_script(
        script_path,
        description_override=readme_descriptions.get(script_path.name),
    )
    port_argument = next(
        (argument for argument in inspection.arguments if argument.primary_name == "--port"),
        None,
    )
    host_argument = next(
        (argument for argument in inspection.arguments if argument.primary_name == "--host"),
        None,
    )
    storage_argument = next(
        (argument for argument in inspection.arguments if argument.primary_name == "--storage-path"),
        None,
    )
    filesystem, dataset, launch_notes = _infer_filesystem_notes(inspection.arguments)

    app = AppDefinition(
        id=identifier,
        name=_titleize(identifier),
        purpose=inspection.description or _description_from_identifier(identifier),
        script_path=str(script_path.relative_to(script_path.parents[1])),
        working_dir=".",
        default_host="127.0.0.1" if host_argument else "127.0.0.1",
        port=PortConfig(
            required=port_argument.required if port_argument else False,
            default=int(port_argument.default) if port_argument and port_argument.default and str(port_argument.default).isdigit() else None,
            configurable=port_argument is not None,
            arg="--port" if port_argument else None,
        ),
        filesystem=FilesystemConfig(
            requires_workspace=filesystem.requires_workspace or storage_argument is not None,
            default_workspace=".sage" if filesystem.requires_workspace or storage_argument else None,
            outputs=(str(storage_argument.default) if storage_argument and storage_argument.default not in {None, "None"} else None),
            notes=filesystem.notes,
        ),
        dataset=dataset,
        verified=False,
        verification_status="discovered",
        tags=sorted(set(inspection.tags)),
        usage=inspection.usage,
        execution_mode=inspection.execution_mode,
        arguments=inspection.arguments,
        examples=inspection.examples,
        environment_variables=inspection.environment_variables,
        launch_notes=_build_launch_notes(inspection.arguments, inspection),
    )
    if inspection.has_http:
        app.start_probe_path = "/"
        app.health_path = "/health" if any(argument.primary_name == "--port" for argument in inspection.arguments) else None
    return app


@lru_cache(maxsize=1)
def discover_apps(root_dir: Path) -> list[AppDefinition]:
    examples_dir = root_dir / "examples"
    definitions: dict[str, AppDefinition] = {}
    for script_path in sorted(examples_dir.glob("run_*.py")):
        identifier = script_path.stem.removeprefix("run_")
        discovered = _build_generic_definition(script_path)
        if identifier in VERIFIED_APPS:
            discovered = _merge_override(discovered, VERIFIED_APPS[identifier])
        discovered = apply_default_argument_values(root_dir, discovered)
        definitions[identifier] = discovered
    return sorted(definitions.values(), key=lambda item: item.id)


def get_app_definition(root_dir: Path, app_id: str) -> AppDefinition:
    for definition in discover_apps(root_dir):
        if definition.id == app_id:
            return definition
    raise KeyError(f"Unknown app id: {app_id}")