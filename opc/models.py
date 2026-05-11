"""Core models for the SAGE OPC control plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import os


@dataclass(slots=True)
class PortConfig:
    required: bool = False
    default: int | None = None
    configurable: bool = False
    arg: str | None = None


@dataclass(slots=True)
class OpenAIRoutes:
    models: bool = False
    chat_completions: bool = False
    completions: bool = False
    embeddings: bool = False


@dataclass(slots=True)
class OpenAICompatibility:
    compatible: bool = False
    base_path: str | None = None
    routes: OpenAIRoutes = field(default_factory=OpenAIRoutes)


@dataclass(slots=True)
class WebUIConfig:
    starts_own_ui: bool = False
    url_template: str | None = None
    open_path: str | None = None


@dataclass(slots=True)
class FilesystemConfig:
    requires_workspace: bool = False
    default_workspace: str | None = None
    outputs: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class DatasetConfig:
    required: bool = False
    notes: str | None = None


@dataclass(slots=True)
class ArgumentDefinition:
    names: list[str]
    primary_name: str
    help: str | None = None
    required: bool = False
    default: str | None = None
    action: str | None = None
    value_name: str | None = None
    choices: list[str] = field(default_factory=list)
    positional: bool = False
    kind: str = "string"
    opc_default_value: str | None = None
    opc_default_origin: str | None = None


@dataclass(slots=True)
class AppDefinition:
    id: str
    name: str
    purpose: str
    script_path: str
    working_dir: str
    command: str = "python"
    default_args: list[str] = field(default_factory=list)
    default_host: str = "127.0.0.1"
    port: PortConfig = field(default_factory=PortConfig)
    openai: OpenAICompatibility = field(default_factory=OpenAICompatibility)
    web_ui: WebUIConfig = field(default_factory=WebUIConfig)
    filesystem: FilesystemConfig = field(default_factory=FilesystemConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    verified: bool = False
    verification_status: str = "untested"
    status_notes: str | None = None
    tags: list[str] = field(default_factory=list)
    start_probe_path: str | None = None
    health_path: str | None = None
    demo_run_path: str | None = None
    usage: str | None = None
    execution_mode: str = "cli"
    arguments: list[ArgumentDefinition] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    environment_variables: list[str] = field(default_factory=list)
    launch_notes: list[str] = field(default_factory=list)

    def build_environment(self, root_dir: Path) -> dict[str, str]:
        env = dict(os.environ)
        app_src = str((root_dir / "apps/src").resolve())
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{app_src}:{existing_pythonpath}" if existing_pythonpath else app_src
        )
        return env

    def build_command(
        self,
        python_executable: str,
        root_dir: Path,
        *,
        host: str | None = None,
        port: int | None = None,
        storage_path: Path | None = None,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        command = [python_executable, str((root_dir / self.script_path).resolve())]
        command.extend(self.default_args)

        resolved_host = host or self.default_host
        if self.port.configurable and self.port.arg and port is not None:
            command.extend([self.port.arg, str(port)])
            command.extend(["--host", resolved_host])

        if storage_path is not None:
            command.extend(["--storage-path", str(storage_path)])

        if extra_args:
            command.extend(extra_args)

        return command

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)