"""Runtime adapter for launching and monitoring SAGE example apps."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re
import shlex
import signal
import socket
import subprocess
import threading
import time
import uuid

import httpx

from .discovery import discover_apps, get_app_definition


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


@dataclass(slots=True)
class LaunchConfig:
    host: str = "127.0.0.1"
    port: int | None = None
    auto_port: bool = True
    storage_path: str | None = None
    extra_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    allow_duplicate: bool = False
    service_mode: bool = False
    startup_timeout_seconds: float = 12.0

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "LaunchConfig":
        payload = payload or {}
        return cls(
            host=payload.get("host") or "127.0.0.1",
            port=payload.get("port"),
            auto_port=payload.get("auto_port", True),
            storage_path=payload.get("storage_path"),
            extra_args=list(payload.get("extra_args") or []),
            env=dict(payload.get("env") or {}),
            allow_duplicate=bool(payload.get("allow_duplicate", False)),
            service_mode=bool(payload.get("service_mode", False)),
            startup_timeout_seconds=float(payload.get("startup_timeout_seconds", 12.0)),
        )


@dataclass(slots=True)
class InlineInputSpec:
    argument: str | None = None
    content: Any = ""
    filename: str | None = None


@dataclass(slots=True)
class InvokeConfig:
    extra_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    inline_inputs: list[InlineInputSpec] = field(default_factory=list)
    timeout_seconds: float = 30.0
    capture_output_preview_chars: int = 12000

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "InvokeConfig":
        payload = payload or {}
        inline_inputs: list[InlineInputSpec] = []
        source_content = payload.get("source")
        prompt_content = payload.get("prompt")
        prompt_argument = payload.get("prompt_argument")
        prompt_filename = payload.get("prompt_filename")
        if source_content is not None or prompt_content is not None:
            inline_inputs.append(
                InlineInputSpec(
                    argument=payload.get("source_argument") or prompt_argument,
                    content=source_content if source_content is not None else prompt_content,
                    filename=payload.get("source_filename") or prompt_filename,
                )
            )
        for entry in payload.get("inline_files") or []:
            if not isinstance(entry, dict):
                continue
            inline_inputs.append(
                InlineInputSpec(
                    argument=entry.get("argument"),
                    content=entry.get("content"),
                    filename=entry.get("filename"),
                )
            )
        return cls(
            extra_args=list(payload.get("extra_args") or []),
            env=dict(payload.get("env") or {}),
            inline_inputs=inline_inputs,
            timeout_seconds=float(payload.get("timeout_seconds", 30.0)),
            capture_output_preview_chars=int(payload.get("capture_output_preview_chars", 12000)),
        )


@dataclass(slots=True)
class LogLine:
    timestamp: str
    stream: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LifecycleEvent:
    timestamp: str
    kind: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompatibilityTestResult:
    name: str
    status: str
    latency_ms: float | None
    last_run: str
    details: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExperimentRecord:
    record_id: str
    timestamp: str
    kind: str
    status: str
    summary: str
    app_id: str | None = None
    app_name: str | None = None
    instance_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RunningInstance:
    instance_id: str
    app_id: str
    app_name: str
    host: str
    port: int | None
    working_dir: str
    command: list[str]
    env: dict[str, str]
    launch_config: LaunchConfig
    endpoint: str | None
    app_ui_url: str | None
    invoke_path: str | None = None
    openai_model: str | None = None
    openai_models_path: str | None = None
    openai_chat_path: str | None = None
    openai_completions_path: str | None = None
    service_mode: bool = False
    status: str = "starting"
    pid: int | None = None
    started_at: str = field(default_factory=_now_iso)
    ended_at: str | None = None
    exit_code: int | None = None
    last_error: str | None = None
    metrics_path: str | None = None
    metrics: dict[str, Any] | None = None
    last_result: dict[str, Any] | None = None
    logs: deque[LogLine] = field(default_factory=lambda: deque(maxlen=4000), repr=False)
    events: list[LifecycleEvent] = field(default_factory=list)
    compatibility: list[CompatibilityTestResult] = field(default_factory=list)
    process: subprocess.Popen[str] | None = field(default=None, repr=False, compare=False)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def uptime_seconds(self) -> float | None:
        if not self.started_at:
            return None
        started = datetime.fromisoformat(self.started_at)
        ended = datetime.fromisoformat(self.ended_at) if self.ended_at else datetime.now(timezone.utc)
        return max((ended - started).total_seconds(), 0.0)

    def to_dict(self, *, include_logs: bool = False) -> dict[str, Any]:
        payload = {
            "instance_id": self.instance_id,
            "app_id": self.app_id,
            "app_name": self.app_name,
            "status": self.status,
            "host": self.host,
            "port": self.port,
            "endpoint": self.endpoint,
            "app_ui_url": self.app_ui_url,
            "invoke_path": self.invoke_path,
            "openai_model": self.openai_model,
            "openai_models_path": self.openai_models_path,
            "openai_chat_path": self.openai_chat_path,
            "openai_completions_path": self.openai_completions_path,
            "service_mode": self.service_mode,
            "pid": self.pid,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "exit_code": self.exit_code,
            "last_error": self.last_error,
            "metrics_path": self.metrics_path,
            "metrics": self.metrics,
            "last_result": self.last_result,
            "command": self.command,
            "working_dir": self.working_dir,
            "env": self.env,
            "launch_config": asdict(self.launch_config),
            "uptime_seconds": self.uptime_seconds(),
            "events": [event.to_dict() for event in self.events[-20:]],
            "compatibility": [test.to_dict() for test in self.compatibility],
        }
        if include_logs:
            payload["logs"] = [line.to_dict() for line in self.logs]
        return payload


class ProcessRuntimeAdapter:
    """Manage app discovery, process launch, logs, and compatibility checks."""

    def __init__(
        self,
        root_dir: Path,
        *,
        python_executable: str,
        port_range_start: int = 18000,
        port_range_end: int = 18100,
    ) -> None:
        self.root_dir = root_dir.resolve()
        self.python_executable = python_executable
        self.port_range_start = port_range_start
        self.port_range_end = port_range_end
        self._instances: dict[str, RunningInstance] = {}
        self._lock = threading.Lock()
        self._experiment_records: deque[ExperimentRecord] = deque(maxlen=800)

    def discover_apps(self) -> list[dict[str, Any]]:
        return [app.to_dict() for app in discover_apps(self.root_dir)]

    def get_app_definition(self, app_id: str):
        return get_app_definition(self.root_dir, app_id)

    def list_instances(self) -> list[dict[str, Any]]:
        with self._lock:
            instances = list(self._instances.values())
        for instance in instances:
            self._refresh_instance_metrics(instance)
        return [instance.to_dict() for instance in sorted(instances, key=lambda item: item.started_at, reverse=True)]

    def get_instance(self, instance_id: str) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        self._refresh_instance_metrics(instance)
        return instance.to_dict(include_logs=True)

    def get_logs(self, instance_id: str, *, stream: str = "merged", limit: int = 200, query: str | None = None) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        logs = list(instance.logs)
        if stream != "merged":
            logs = [line for line in logs if line.stream == stream]
        if query:
            lowered = query.lower()
            logs = [line for line in logs if lowered in line.message.lower()]
        logs = logs[-limit:]
        return {
            "instance_id": instance_id,
            "stream": stream,
            "count": len(logs),
            "logs": [line.to_dict() for line in logs],
        }

    def validate_launch_config(self, app_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        app = self.get_app_definition(app_id)
        launch_config = LaunchConfig.from_payload(payload)
        deferred_service_mode = launch_config.service_mode and app.execution_mode != "http"
        resolved_extra_args = (
            self._strip_service_mode_required_arguments(app, launch_config.extra_args)
            if deferred_service_mode
            else self._apply_default_required_arguments(app, launch_config.extra_args)
        )
        host = launch_config.host or app.default_host
        resolved_port = self._resolve_port(app, launch_config)
        storage_path = self._resolve_storage_path(app, launch_config)
        working_dir = (self.root_dir / app.working_dir).resolve()
        script_path = (self.root_dir / app.script_path).resolve()
        duplicate_running = any(
            instance.app_id == app_id and instance.status in {"starting", "running", "degraded", "stopping"}
            for instance in self._instances.values()
        )
        missing_required_args = self._missing_required_arguments(app, resolved_extra_args)
        missing_env_vars = [
            env_name
            for env_name in app.environment_variables
            if env_name not in os.environ and env_name not in launch_config.env
        ]

        checks = [
            {
                "name": "app_definition_exists",
                "passed": True,
                "blocking": True,
                "detail": f"Discovered app '{app_id}'.",
            },
            {
                "name": "python_executable_exists",
                "passed": Path(self.python_executable).exists(),
                "blocking": True,
                "detail": self.python_executable,
            },
            {
                "name": "working_directory_exists",
                "passed": working_dir.exists(),
                "blocking": True,
                "detail": str(working_dir),
            },
            {
                "name": "script_exists",
                "passed": script_path.exists(),
                "blocking": True,
                "detail": str(script_path),
            },
            {
                "name": "duplicate_instance_check",
                "passed": launch_config.allow_duplicate or not duplicate_running,
                "blocking": True,
                "detail": "No active instance conflict." if not duplicate_running else "Another live instance already exists.",
            },
            {
                "name": "required_arguments_present",
                "passed": deferred_service_mode or not missing_required_args,
                "blocking": True,
                "detail": (
                    "Required CLI arguments will be provided later through the instance invoke endpoint."
                    if deferred_service_mode
                    else (
                        "All required CLI arguments are satisfied."
                        if not missing_required_args
                        else "Missing required arguments: " + ", ".join(missing_required_args)
                    )
                ),
            },
        ]

        if deferred_service_mode:
            checks.append(
                {
                    "name": "service_mode_enabled",
                    "passed": True,
                    "blocking": False,
                    "detail": "Launch will register a reusable invoke endpoint instead of immediately executing the batch pipeline.",
                }
            )

        if app.port.required or resolved_port is not None:
            checks.append(
                {
                    "name": "port_available",
                    "passed": resolved_port is not None and self._is_port_available(host, resolved_port),
                    "blocking": True,
                    "detail": (
                        f"Resolved port {resolved_port} is available."
                        if resolved_port is not None and self._is_port_available(host, resolved_port)
                        else "No available port could be resolved in the configured range."
                    ),
                }
            )

        if storage_path is not None:
            checks.append(
                {
                    "name": "storage_parent_ready",
                    "passed": storage_path.parent.exists() or storage_path.parent.parent.exists(),
                    "blocking": False,
                    "detail": str(storage_path),
                }
            )

        if app.environment_variables:
            checks.append(
                {
                    "name": "environment_variables_present",
                    "passed": not missing_env_vars,
                    "blocking": False,
                    "detail": (
                        "All documented environment variables are present."
                        if not missing_env_vars
                        else "Missing documented environment variables: " + ", ".join(missing_env_vars)
                    ),
                }
            )

        if app.execution_mode == "interactive":
            checks.append(
                {
                    "name": "interactive_entrypoint_notice",
                    "passed": True,
                    "blocking": False,
                    "detail": "This script starts an interactive console flow unless one-shot flags are provided.",
                }
            )

        command = app.build_command(
            self.python_executable,
            self.root_dir,
            host=host,
            port=resolved_port,
            storage_path=storage_path,
            extra_args=resolved_extra_args,
        )
        env_preview = app.build_environment(self.root_dir)
        env_preview.update(launch_config.env)

        endpoint_preview = (
            f"http://{host}:{resolved_port}" if resolved_port is not None else None
        )
        app_ui_preview = None
        if endpoint_preview and app.web_ui.starts_own_ui and app.web_ui.open_path:
            app_ui_preview = f"{endpoint_preview}{app.web_ui.open_path}"

        return {
            "app": app.to_dict(),
            "resolved_host": host,
            "resolved_port": resolved_port,
            "storage_path": str(storage_path) if storage_path is not None else None,
            "resolved_extra_args": resolved_extra_args,
            "command": command,
            "command_preview": self._format_command_preview(command, working_dir, env_preview),
            "environment_preview": {
                key: value
                for key, value in env_preview.items()
                if key in {"PYTHONPATH", "SAGE_SUPPLY_CHAIN_MODEL", "SAGE_SUPPLY_CHAIN_BASE_URL", "SAGE_SUPPLY_CHAIN_API_KEY"}
                or key in launch_config.env
            },
            "endpoint_preview": endpoint_preview,
            "app_ui_preview": app_ui_preview,
            "invoke_path_preview": "/api/instances/<instance_id>/invoke" if deferred_service_mode else None,
            "checks": checks,
        }

    def launch_app(self, app_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        app = self.get_app_definition(app_id)
        validation = self.validate_launch_config(app_id, payload)
        failures = [check for check in validation["checks"] if check["blocking"] and not check["passed"]]
        if failures:
            self._record_experiment(
                "launch",
                "failed",
                failures[0]["detail"],
                app_id=app.id,
                app_name=app.name,
                details={"blocking_checks": failures},
            )
            raise ValueError(failures[0]["detail"])

        launch_config = LaunchConfig.from_payload(payload)
        launch_config.extra_args = list(validation["resolved_extra_args"])
        host = validation["resolved_host"]
        port = validation["resolved_port"]
        storage_path = Path(validation["storage_path"]) if validation["storage_path"] else None
        working_dir = (self.root_dir / app.working_dir).resolve()
        env = app.build_environment(self.root_dir)
        env.update(launch_config.env)

        if storage_path is not None:
            storage_path.parent.mkdir(parents=True, exist_ok=True)

        command = app.build_command(
            self.python_executable,
            self.root_dir,
            host=host,
            port=port,
            storage_path=storage_path,
            extra_args=launch_config.extra_args,
        )

        if launch_config.service_mode and app.execution_mode != "http":
            instance_id = uuid.uuid4().hex[:12]
            instance = RunningInstance(
                instance_id=instance_id,
                app_id=app_id,
                app_name=app.name,
                host=host,
                port=None,
                working_dir=str(working_dir),
                command=command,
                env=env,
                launch_config=launch_config,
                endpoint=None,
                app_ui_url=None,
                invoke_path=f"/api/instances/{instance_id}/invoke",
                openai_model=instance_id,
                openai_models_path="/v1/models",
                openai_chat_path="/v1/chat/completions",
                openai_completions_path="/v1/completions",
                service_mode=True,
                status="running",
                pid=None,
                process=None,
            )
            self._record_event(instance, "service_registered", "Invoke service endpoint registered.")
            with self._lock:
                self._instances[instance_id] = instance
            self._record_experiment(
                "launch",
                "passed",
                "Service-mode instance registered for reusable invocation.",
                app_id=app.id,
                app_name=app.name,
                instance_id=instance_id,
                details={
                    "service_mode": True,
                    "invoke_path": instance.invoke_path,
                    "extra_args": launch_config.extra_args,
                },
            )
            return instance.to_dict()

        instance_id = uuid.uuid4().hex[:12]
        metrics_path = self._metrics_path_for_process_run(app.id, instance_id)
        env["SAGE_OPERATOR_METRICS_PATH"] = str(metrics_path)

        process = subprocess.Popen(
            command,
            cwd=str(working_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )

        endpoint = f"http://{host}:{port}" if port is not None else None
        app_ui_url = None
        if endpoint and app.web_ui.starts_own_ui and app.web_ui.open_path:
            app_ui_url = f"{endpoint}{app.web_ui.open_path}"

        instance = RunningInstance(
            instance_id=instance_id,
            app_id=app_id,
            app_name=app.name,
            host=host,
            port=port,
            working_dir=str(working_dir),
            command=command,
            env=env,
            launch_config=launch_config,
            endpoint=endpoint,
            app_ui_url=app_ui_url,
            invoke_path=None,
            openai_model=None,
            openai_models_path=None,
            openai_chat_path=None,
            openai_completions_path=None,
            service_mode=False,
            pid=process.pid,
            metrics_path=str(metrics_path),
            process=process,
        )
        self._record_event(instance, "process_started", "Process started.", {"pid": process.pid})
        with self._lock:
            self._instances[instance_id] = instance

        self._start_pipe_reader(instance, "stdout", process.stdout)
        self._start_pipe_reader(instance, "stderr", process.stderr)
        self._start_process_watcher(instance)

        if self._wait_until_ready(instance, timeout_seconds=launch_config.startup_timeout_seconds):
            self._record_event(instance, "readiness_probe_passed", "Startup probe passed.")
        elif instance.process and instance.process.poll() is None:
            with instance.lock:
                instance.status = "degraded"
                instance.last_error = "Startup probe timed out."
            self._record_event(instance, "startup_timeout", "Startup probe timed out.")

        launch_status = instance.status
        if launch_status == "starting":
            launch_status = "failed" if instance.process and instance.process.poll() is not None else "warning"
        self._record_experiment(
            "launch",
            launch_status,
            "HTTP/CLI instance launched through OPC runtime.",
            app_id=app.id,
            app_name=app.name,
            instance_id=instance_id,
            details={
                "endpoint": instance.endpoint,
                "app_ui_url": instance.app_ui_url,
                "port": instance.port,
                "service_mode": False,
            },
        )

        return instance.to_dict()

    def invoke_app(self, app_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        app = self.get_app_definition(app_id)
        invoke_config = InvokeConfig.from_payload(payload)
        result = self._invoke_app_definition(app, invoke_config)
        self._record_experiment(
            "invoke",
            "passed" if result["success"] else "failed",
            "One-shot app invocation completed.",
            app_id=app.id,
            app_name=app.name,
            details={
                "return_code": result["return_code"],
                "duration_ms": result["duration_ms"],
                "success": result["success"],
                "metrics_available": bool(result.get("metrics")),
                "stage_count": len((result.get("metrics") or {}).get("stages") or []),
            },
        )
        return result

    def invoke_instance(self, instance_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        if not instance.service_mode:
            raise ValueError("This instance was not launched in service mode. Launch it with service_mode=true first.")

        app = self.get_app_definition(instance.app_id)
        invoke_config = InvokeConfig.from_payload(payload)
        storage_path = (
            Path(instance.launch_config.storage_path).expanduser().resolve()
            if instance.launch_config.storage_path
            else None
        )
        result = self._invoke_app_definition(
            app,
            invoke_config,
            base_extra_args=instance.launch_config.extra_args,
            base_env=instance.launch_config.env,
            storage_path=storage_path,
        )
        self._record_event(
            instance,
            "invoke_completed",
            "One-shot invocation completed through instance endpoint.",
            {"success": result["success"], "return_code": result["return_code"]},
        )
        with instance.lock:
            instance.metrics = result.get("metrics")
            instance.metrics_path = result.get("metrics_path") or instance.metrics_path
            instance.last_result = {
                key: value
                for key, value in result.items()
                if key
                in {
                    "success",
                    "return_code",
                    "duration_ms",
                    "artifacts_dir",
                    "command_preview",
                    "stdout",
                    "stderr",
                    "materialized_inputs",
                    "output_artifacts",
                    "metrics",
                    "metrics_path",
                }
            }
        self._record_experiment(
            "invoke",
            "passed" if result["success"] else "failed",
            "Instance invoke completed through reusable endpoint.",
            app_id=app.id,
            app_name=app.name,
            instance_id=instance.instance_id,
            details={
                "return_code": result["return_code"],
                "duration_ms": result["duration_ms"],
                "success": result["success"],
                "metrics_available": bool(result.get("metrics")),
                "stage_count": len((result.get("metrics") or {}).get("stages") or []),
            },
        )
        return result

    def list_openai_models(self) -> dict[str, Any]:
        models = []
        for instance in self._instances.values():
            if not instance.service_mode or instance.status not in {"running", "degraded"}:
                continue
            models.append(
                {
                    "id": instance.openai_model or instance.instance_id,
                    "object": "model",
                    "created": int(datetime.fromisoformat(instance.started_at).timestamp()),
                    "owned_by": "sage-opc",
                    "permission": [],
                    "root": instance.app_id,
                    "parent": None,
                    "metadata": {
                        "instance_id": instance.instance_id,
                        "app_id": instance.app_id,
                        "invoke_path": instance.invoke_path,
                    },
                }
            )
        return {"object": "list", "data": models}

    def openai_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        model_id = payload.get("model")
        if not model_id:
            raise ValueError("OpenAI chat request must include a model.")

        instance = self._get_service_instance_by_model(model_id)
        prompt = self._openai_messages_to_prompt(payload.get("messages") or [])
        invoke_payload = self._openai_payload_to_invoke_payload(payload, prompt_key="prompt", prompt_value=prompt)
        result = self.invoke_instance(instance.instance_id, invoke_payload)
        content = self._openai_response_content(result)
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": self._openai_usage(prompt, content),
            "opc_result": result,
        }

    def openai_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        model_id = payload.get("model")
        if not model_id:
            raise ValueError("OpenAI completion request must include a model.")

        instance = self._get_service_instance_by_model(model_id)
        prompt = payload.get("prompt")
        if isinstance(prompt, list):
            prompt = "\n".join(str(item) for item in prompt)
        prompt = "" if prompt is None else str(prompt)
        invoke_payload = self._openai_payload_to_invoke_payload(payload, prompt_key="prompt", prompt_value=prompt)
        result = self.invoke_instance(instance.instance_id, invoke_payload)
        text = self._openai_response_content(result)
        return {
            "id": f"cmpl-{uuid.uuid4().hex[:24]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "text": text,
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "usage": self._openai_usage(prompt, text),
            "opc_result": result,
        }

    def _invoke_app_definition(
        self,
        app,
        invoke_config: InvokeConfig,
        *,
        base_extra_args: list[str] | None = None,
        base_env: dict[str, str] | None = None,
        storage_path: Path | None = None,
    ) -> dict[str, Any]:
        if app.execution_mode == "http":
            raise ValueError("One-shot invoke is for batch or CLI pipelines. Use /launch for HTTP apps.")

        working_dir = (self.root_dir / app.working_dir).resolve()
        env = app.build_environment(self.root_dir)
        if base_env:
            env.update(base_env)
        env.update(invoke_config.env)

        prepared = self._prepare_inline_invocation(app, invoke_config, base_extra_args=base_extra_args)
        metrics_path = prepared["run_dir"] / "metrics.json"
        env["SAGE_OPERATOR_METRICS_PATH"] = str(metrics_path)
        missing_required_args = self._missing_required_arguments(app, prepared["extra_args"])
        if missing_required_args:
            raise ValueError(
                "Missing required arguments for one-shot invoke: " + ", ".join(missing_required_args)
            )

        command = app.build_command(
            self.python_executable,
            self.root_dir,
            storage_path=storage_path,
            extra_args=prepared["extra_args"],
        )

        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=str(working_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=invoke_config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(f"One-shot invocation timed out after {invoke_config.timeout_seconds:.1f}s.") from exc

        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        output_artifacts = [
            self._describe_artifact(path, argument, invoke_config.capture_output_preview_chars)
            for argument, path in prepared["output_paths"]
        ]
        metrics = self._read_metrics_artifact(metrics_path)

        return {
            "app": app.to_dict(),
            "success": completed.returncode == 0,
            "return_code": completed.returncode,
            "duration_ms": duration_ms,
            "working_dir": str(working_dir),
            "artifacts_dir": str(prepared["run_dir"]),
            "command": command,
            "command_preview": self._format_command_preview(command, working_dir, env),
            "stdout": self._trim_preview(completed.stdout, invoke_config.capture_output_preview_chars),
            "stderr": self._trim_preview(completed.stderr, invoke_config.capture_output_preview_chars),
            "materialized_inputs": prepared["materialized_inputs"],
            "output_artifacts": output_artifacts,
            "metrics_path": str(metrics_path),
            "metrics": metrics,
        }

    def stop_app(self, instance_id: str, *, timeout_seconds: float = 5.0) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        if instance.process is None or instance.process.poll() is not None:
            with instance.lock:
                instance.status = "stopped"
                instance.ended_at = instance.ended_at or _now_iso()
                instance.last_error = None
            self._record_experiment(
                "stop",
                "passed",
                "Instance marked stopped.",
                app_id=instance.app_id,
                app_name=instance.app_name,
                instance_id=instance.instance_id,
                details={"uptime_seconds": instance.uptime_seconds()},
            )
            return instance.to_dict()

        with instance.lock:
            instance.status = "stopping"
        self._record_event(instance, "stop_requested", "Stop requested by control plane.")

        try:
            os.killpg(os.getpgid(instance.process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if instance.process.poll() is not None:
                break
            time.sleep(0.2)

        if instance.process.poll() is None:
            self._record_event(instance, "kill_requested", "SIGTERM timed out; sending SIGKILL.")
            try:
                os.killpg(os.getpgid(instance.process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass

        with instance.lock:
            instance.ended_at = instance.ended_at or _now_iso()
            instance.status = "stopped"
            instance.last_error = None

        self._record_experiment(
            "stop",
            "passed",
            "Instance stopped by OPC control action.",
            app_id=instance.app_id,
            app_name=instance.app_name,
            instance_id=instance.instance_id,
            details={"uptime_seconds": instance.uptime_seconds()},
        )

        return instance.to_dict()

    def stop_all(self) -> None:
        for instance_id in list(self._instances):
            try:
                self.stop_app(instance_id, timeout_seconds=1.0)
            except KeyError:
                continue

    def restart_app(self, instance_id: str) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        payload = asdict(instance.launch_config)
        app_id = instance.app_id
        old_instance_id = instance.instance_id
        self.stop_app(instance_id)
        result = self.launch_app(app_id, payload)
        self._record_experiment(
            "restart",
            "passed",
            "Instance restarted through OPC control action.",
            app_id=app_id,
            app_name=result["app_name"],
            instance_id=result["instance_id"],
            details={"previous_instance_id": old_instance_id, "new_instance_id": result["instance_id"]},
        )
        return result

    def run_instance_demo(self, instance_id: str) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        app = self.get_app_definition(instance.app_id)
        if instance.endpoint is None:
            raise ValueError("This instance has no HTTP endpoint to exercise.")
        if not app.demo_run_path:
            raise ValueError("This app does not declare a demo flow for OPC to run.")
        if instance.status not in {"running", "degraded"}:
            raise ValueError("This instance is not ready to accept demo traffic.")

        url = f"{instance.endpoint}{app.demo_run_path}"
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=60.0, follow_redirects=True) as client:
                response = client.post(url)
        except httpx.HTTPError as exc:
            self._record_event(instance, "demo_run_failed", "HTTP demo request failed.", {"url": url, "error": str(exc)})
            self._record_experiment(
                "invoke",
                "failed",
                "HTTP demo request failed.",
                app_id=instance.app_id,
                app_name=instance.app_name,
                instance_id=instance.instance_id,
                details={"url": url, "error": str(exc)},
            )
            raise ValueError(f"Demo request failed: {exc}") from exc

        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        if response.status_code >= 400:
            detail = f"{response.status_code} {response.reason_phrase}".strip()
            self._record_event(instance, "demo_run_failed", "HTTP demo request returned an error status.", {"url": url, "status": response.status_code})
            self._record_experiment(
                "invoke",
                "failed",
                "HTTP demo request returned an error status.",
                app_id=instance.app_id,
                app_name=instance.app_name,
                instance_id=instance.instance_id,
                details={"url": url, "status": response.status_code},
            )
            raise ValueError(f"Demo request failed: {detail}")

        response_json: Any | None = None
        response_text_preview: str | None = None
        try:
            response_json = response.json()
        except ValueError:
            response_text_preview = self._trim_preview(response.text, 12000)

        metrics = self._wait_for_metrics_artifact(Path(instance.metrics_path) if instance.metrics_path else None, timeout_seconds=2.0)
        result = {
            "success": True,
            "duration_ms": duration_ms,
            "http_status": response.status_code,
            "command_preview": f"POST {url}",
            "request": {"method": "POST", "url": url},
            "response_json": response_json,
            "response_text_preview": response_text_preview,
            "materialized_inputs": [],
            "output_artifacts": [],
            "metrics_path": instance.metrics_path,
            "metrics": metrics,
        }
        with instance.lock:
            instance.metrics = metrics or instance.metrics
            instance.last_result = result
        self._record_event(
            instance,
            "demo_run_completed",
            "HTTP demo request completed.",
            {
                "url": url,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "metrics_available": bool(metrics and metrics.get("stages")),
            },
        )
        self._record_experiment(
            "invoke",
            "passed",
            "HTTP demo request completed through OPC.",
            app_id=instance.app_id,
            app_name=instance.app_name,
            instance_id=instance.instance_id,
            details={
                "url": url,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "metrics_available": bool(metrics and metrics.get("stages")),
                "stage_count": len((metrics or {}).get("stages") or []),
            },
        )
        return result

    def run_compatibility_check(self, instance_id: str) -> dict[str, Any]:
        instance = self._get_instance(instance_id)
        app = self.get_app_definition(instance.app_id)
        tests: list[CompatibilityTestResult] = []

        if instance.endpoint is None:
            tests.append(
                CompatibilityTestResult(
                    name="Start command",
                    status="passed" if instance.status in {"running", "degraded", "stopped"} else "failed",
                    latency_ms=None,
                    last_run=_now_iso(),
                    details="CLI app has no HTTP endpoint; only process status checked.",
                )
            )
        else:
            tests.append(self._http_check("GET /", f"{instance.endpoint}/"))
            if app.health_path:
                tests.append(self._http_check(f"GET {app.health_path}", f"{instance.endpoint}{app.health_path}"))
            if app.web_ui.starts_own_ui and app.web_ui.open_path:
                tests.append(
                    self._http_check(
                        f"GET {app.web_ui.open_path}",
                        f"{instance.endpoint}{app.web_ui.open_path}",
                    )
                )
            if app.openai.compatible and app.openai.base_path:
                base_path = app.openai.base_path.rstrip("/")
                if app.openai.routes.models:
                    tests.append(self._http_check("GET /v1/models", f"{instance.endpoint}{base_path}/models"))
                if app.openai.routes.chat_completions:
                    tests.append(
                        self._http_check(
                            "POST /v1/chat/completions",
                            f"{instance.endpoint}{base_path}/chat/completions",
                            method="POST",
                            json_payload={
                                "model": "default",
                                "messages": [{"role": "user", "content": "Hello from SAGE OPC"}],
                            },
                        )
                    )
            else:
                for route_name in [
                    "GET /v1/models",
                    "POST /v1/chat/completions",
                    "POST /v1/completions",
                    "POST /v1/embeddings",
                ]:
                    tests.append(
                        CompatibilityTestResult(
                            name=route_name,
                            status="skipped",
                            latency_ms=None,
                            last_run=_now_iso(),
                            details="Route is not declared as OpenAI-compatible for this app.",
                        )
                    )

        instance.compatibility = tests
        self._record_event(instance, "compatibility_check", "Compatibility checks completed.")
        overall = self._compatibility_overall(tests)
        self._record_experiment(
            "compatibility",
            overall,
            "Compatibility checks executed for instance.",
            app_id=instance.app_id,
            app_name=instance.app_name,
            instance_id=instance.instance_id,
            details={"overall": overall, "test_count": len(tests)},
        )
        return {
            "instance_id": instance_id,
            "overall": overall,
            "tests": [test.to_dict() for test in tests],
        }

    def list_ports(self) -> dict[str, Any]:
        used = []
        for instance in self._instances.values():
            if instance.port is None or instance.status not in {"starting", "running", "degraded", "stopping"}:
                continue
            used.append(
                {
                    "port": instance.port,
                    "instance_id": instance.instance_id,
                    "app_name": instance.app_name,
                    "status": instance.status,
                }
            )

        available_preview = []
        for candidate in range(self.port_range_start, self.port_range_end + 1):
            if self._is_port_available("127.0.0.1", candidate):
                available_preview.append(candidate)
            if len(available_preview) >= 12:
                break

        return {
            "range_start": self.port_range_start,
            "range_end": self.port_range_end,
            "used": sorted(used, key=lambda item: item["port"]),
            "available_count": sum(
                1
                for candidate in range(self.port_range_start, self.port_range_end + 1)
                if self._is_port_available("127.0.0.1", candidate)
            ),
            "available_preview": available_preview,
        }

    def settings(self) -> dict[str, Any]:
        return {
            "root_dir": str(self.root_dir),
            "python_executable": self.python_executable,
            "allowed_port_range": [self.port_range_start, self.port_range_end],
            "default_host": "127.0.0.1",
            "log_retention_lines": 4000,
            "notes": "Child processes inherit the OPC server Python interpreter and inject apps/src into PYTHONPATH.",
        }

    def list_experiments(self) -> dict[str, Any]:
        records = list(self._experiment_records)
        exercised_apps = sorted({record.app_id for record in records if record.app_id})
        active_instances = sum(
            1
            for instance in self._instances.values()
            if instance.status in {"starting", "running", "degraded", "stopping"}
        )
        return {
            "summary": {
                "total_events": len(records),
                "launches": sum(1 for record in records if record.kind == "launch"),
                "invocations": sum(1 for record in records if record.kind == "invoke"),
                "control_actions": sum(
                    1 for record in records if record.kind in {"stop", "restart", "compatibility"}
                ),
                "failures": sum(1 for record in records if record.status == "failed"),
                "apps_exercised": len(exercised_apps),
                "active_instances": active_instances,
                "last_event_at": records[-1].timestamp if records else None,
                "capture_policy": (
                    "Launch, invoke, stop, restart, and compatibility checks are captured automatically. "
                    "High-frequency live validation is intentionally excluded to avoid noisy experiment logs."
                ),
            },
            "apps": exercised_apps,
            "records": [record.to_dict() for record in reversed(records)],
        }

    def reset_experiments(self) -> dict[str, Any]:
        self._experiment_records.clear()
        return self.list_experiments()

    def export_experiments_json(self) -> str:
        return json.dumps(self.list_experiments(), ensure_ascii=False, indent=2)

    def export_inventory_markdown(self) -> str:
        lines = [
            "# SAGE Examples App Inventory",
            "",
            "Generated by SAGE OPC from sage-examples discovery metadata.",
            "",
            "| App | Purpose | Start Command | Working Dir | Port Configurable | Starts Web UI | OpenAI-Compatible | Filesystem Needs | Dataset Needs | Stop Method | Status |",
            "|---|---|---|---|---:|---:|---:|---|---|---|---|",
        ]
        for app in discover_apps(self.root_dir):
            command = f"python {app.script_path}"
            if app.port.configurable and app.port.arg and app.port.default is not None:
                command = f"{command} {app.port.arg} {app.port.default}"
            lines.append(
                "| {id} | {purpose} | `{command}` | `{cwd}` | {port} | {web} | {openai} | {fs} | {dataset} | {stop} | {status} |".format(
                    id=app.id,
                    purpose=app.purpose,
                    command=command,
                    cwd=app.working_dir,
                    port=_format_bool(app.port.configurable),
                    web=_format_bool(app.web_ui.starts_own_ui),
                    openai=("yes" if app.openai.compatible else "no"),
                    fs=app.filesystem.notes or ("workspace" if app.filesystem.requires_workspace else "none"),
                    dataset=app.dataset.notes or ("required" if app.dataset.required else "none"),
                    stop="SIGTERM with SIGKILL fallback",
                    status=app.verification_status,
                )
            )
        lines.extend([
            "",
            "## Launch Notes",
            "",
        ])
        for app in discover_apps(self.root_dir):
            lines.append(f"### {app.name}")
            lines.append("")
            lines.append(f"- Execution mode: {app.execution_mode}")
            lines.append(f"- Usage: `{app.usage or f'python {app.script_path}'}`")
            if app.arguments:
                required_args = [argument.primary_name for argument in app.arguments if argument.required]
                lines.append(
                    "- Required args: " + (", ".join(required_args) if required_args else "none")
                )
            if app.environment_variables:
                lines.append("- Environment variables: " + ", ".join(app.environment_variables))
            if app.examples:
                lines.append("- Example: `" + app.examples[0] + "`")
            if app.launch_notes:
                for note in app.launch_notes[:3]:
                    lines.append("- " + note)
            lines.append("")
        return "\n".join(lines)

    def export_compatibility_markdown(self) -> str:
        lines = [
            "# SAGE OPC Compatibility Matrix",
            "",
            "| App | Terminal Start | Port Override | HTTP | Own Web UI | OpenAI API | Filesystem | Dataset | Stop/Restart | Overall |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for app in discover_apps(self.root_dir):
            http_capable = app.port.required or app.web_ui.starts_own_ui or app.health_path is not None
            overall = app.verification_status
            lines.append(
                "| {id} | {start} | {port} | {http} | {web} | {openai} | {fs} | {dataset} | {restart} | {overall} |".format(
                    id=app.id,
                    start="verified" if app.verified else "discovered",
                    port="yes" if app.port.configurable else "no",
                    http="yes" if http_capable else "no",
                    web="yes" if app.web_ui.starts_own_ui else "no",
                    openai="yes" if app.openai.compatible else "no",
                    fs="yes" if app.filesystem.requires_workspace else "no",
                    dataset="yes" if app.dataset.required else "no",
                    restart="yes",
                    overall=overall,
                )
            )
        return "\n".join(lines)

    def _get_instance(self, instance_id: str) -> RunningInstance:
        try:
            return self._instances[instance_id]
        except KeyError as exc:
            raise KeyError(f"Unknown instance id: {instance_id}") from exc

    def _refresh_instance_metrics(self, instance: RunningInstance) -> None:
        if not instance.metrics_path:
            return
        metrics = self._read_metrics_artifact(Path(instance.metrics_path))
        if metrics is None:
            return
        with instance.lock:
            instance.metrics = metrics
            if instance.last_result is not None:
                instance.last_result["metrics"] = metrics
                instance.last_result["metrics_path"] = instance.metrics_path

    def _resolve_port(self, app, launch_config: LaunchConfig) -> int | None:
        if not app.port.required and launch_config.port is None:
            return None

        if not launch_config.auto_port:
            return launch_config.port or app.port.default

        preferred = launch_config.port or app.port.default
        if preferred is not None and self._is_port_available(launch_config.host, preferred):
            return preferred

        for candidate in range(self.port_range_start, self.port_range_end + 1):
            if self._is_port_available(launch_config.host, candidate):
                return candidate
        return None

    def _resolve_storage_path(self, app, launch_config: LaunchConfig) -> Path | None:
        if launch_config.storage_path:
            return Path(launch_config.storage_path).expanduser().resolve()
        if app.filesystem.outputs:
            return (self.root_dir / app.filesystem.outputs).resolve()
        return None

    def _apply_default_required_arguments(self, app, extra_args: list[str]) -> list[str]:
        resolved = list(extra_args)
        provided_values = self._provided_option_values(app, resolved)
        for argument in app.arguments:
            if not argument.required or argument.positional or argument.kind != "path":
                continue
            if argument.primary_name in provided_values:
                continue
            if argument.opc_default_value:
                resolved.extend([argument.primary_name, argument.opc_default_value])
                provided_values[argument.primary_name] = argument.opc_default_value
        return resolved

    def _strip_service_mode_required_arguments(self, app, extra_args: list[str]) -> list[str]:
        removable_arguments = {
            argument.primary_name
            for argument in app.arguments
            if argument.required and not argument.positional and argument.kind == "path"
        }
        resolved: list[str] = []
        index = 0
        while index < len(extra_args):
            token = extra_args[index]
            matched_argument = next(
                (
                    argument
                    for argument in app.arguments
                    if any(token == name or token.startswith(name + "=") for name in argument.names)
                ),
                None,
            )
            if matched_argument is None or matched_argument.primary_name not in removable_arguments:
                resolved.append(token)
                index += 1
                continue
            if matched_argument.action in {"store_true", "store_false"} or "=" in token:
                index += 1
                continue
            index += 2
        return resolved

    def _prepare_inline_invocation(
        self,
        app,
        invoke_config: InvokeConfig,
        *,
        base_extra_args: list[str] | None = None,
    ) -> dict[str, Any]:
        run_dir = (
            self.root_dir
            / ".sage"
            / "opc-oneshot"
            / app.id
            / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        extra_args = list(base_extra_args or [])
        extra_args.extend(invoke_config.extra_args)
        provided_values = self._provided_option_values(app, extra_args)
        materialized_inputs: list[dict[str, Any]] = []

        for inline_input in invoke_config.inline_inputs:
            argument = self._resolve_inline_argument(app, inline_input.argument)
            if argument.primary_name in provided_values:
                raise ValueError(
                    f"Inline input for {argument.primary_name} conflicts with an explicit argument value."
                )
            if argument.action in {"store_true", "store_false"}:
                raise ValueError(f"Inline input is not supported for flag argument {argument.primary_name}.")

            rendered_content = self._render_inline_content(inline_input.content)
            if argument.kind == "path":
                filename = self._choose_inline_filename(argument.primary_name, inline_input.filename, rendered_content)
                input_path = run_dir / "inputs" / filename
                input_path.parent.mkdir(parents=True, exist_ok=True)
                input_path.write_text(rendered_content, encoding="utf-8")
                value = str(input_path)
                materialized_inputs.append(
                    {
                        "argument": argument.primary_name,
                        "path": value,
                        "size_bytes": len(rendered_content.encode("utf-8")),
                    }
                )
            else:
                value = rendered_content
                materialized_inputs.append(
                    {
                        "argument": argument.primary_name,
                        "value_preview": self._trim_preview(rendered_content, 240),
                    }
                )
            extra_args.extend([argument.primary_name, value])
            provided_values[argument.primary_name] = value

        for argument in self._required_output_arguments(app):
            if argument.primary_name in provided_values:
                continue
            output_path = run_dir / "outputs" / self._default_output_filename(app, argument.primary_name, extra_args)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            extra_args.extend([argument.primary_name, str(output_path)])
            provided_values[argument.primary_name] = str(output_path)

        output_paths = [
            (argument.primary_name, Path(path_value).expanduser().resolve())
            for argument, path_value in self._provided_path_values(app, extra_args)
            if self._is_output_argument(argument)
        ]

        return {
            "run_dir": run_dir,
            "extra_args": extra_args,
            "materialized_inputs": materialized_inputs,
            "output_paths": output_paths,
        }

    def _missing_required_arguments(self, app, extra_args: list[str]) -> list[str]:
        dedicated_args = {"--host", "--port", "--storage-path"}
        provided_options: set[str] = set()
        positional_values: list[str] = []
        index = 0
        while index < len(extra_args):
            token = extra_args[index]
            matched_argument = next(
                (
                    argument
                    for argument in app.arguments
                    if any(token == name or token.startswith(name + "=") for name in argument.names)
                ),
                None,
            )
            if matched_argument is not None:
                provided_options.add(matched_argument.primary_name)
                if matched_argument.action not in {"store_true", "store_false"} and "=" not in token and index + 1 < len(extra_args):
                    index += 2
                    continue
                index += 1
                continue
            if token.startswith("-"):
                index += 1
                continue
            positional_values.append(token)
            index += 1

        missing: list[str] = []
        positional_required = [
            argument for argument in app.arguments if argument.required and argument.positional
        ]
        if len(positional_values) < len(positional_required):
            missing.extend(argument.primary_name for argument in positional_required[len(positional_values):])

        for argument in app.arguments:
            if not argument.required or argument.positional:
                continue
            if argument.primary_name in dedicated_args:
                continue
            if argument.primary_name not in provided_options:
                missing.append(argument.primary_name)
        return missing

    def _required_output_arguments(self, app) -> list[Any]:
        return [
            argument
            for argument in app.arguments
            if argument.required and not argument.positional and argument.kind == "path" and self._is_output_argument(argument)
        ]

    def _is_output_argument(self, argument) -> bool:
        lowered = " ".join(
            part.lower()
            for part in [argument.primary_name, argument.help or "", argument.value_name or ""]
            if part
        )
        return "output" in lowered or "out-file" in lowered or "outfile" in lowered

    def _resolve_inline_argument(self, app, requested_argument: str | None):
        if requested_argument:
            argument = self._find_argument_definition(app, requested_argument)
            if argument is None:
                raise ValueError(f"Unknown inline input argument: {requested_argument}")
            return argument

        candidates = [
            argument
            for argument in app.arguments
            if argument.kind == "path" and not argument.positional and not self._is_output_argument(argument)
        ]
        required_candidates = [argument for argument in candidates if argument.required]
        if len(required_candidates) == 1:
            return required_candidates[0]
        if len(candidates) == 1:
            return candidates[0]
        candidate_names = ", ".join(argument.primary_name for argument in candidates) or "none"
        raise ValueError(
            "Inline input must specify a target argument. Candidates: " + candidate_names
        )

    def _find_argument_definition(self, app, requested_argument: str):
        return next(
            (
                argument
                for argument in app.arguments
                if requested_argument == argument.primary_name or requested_argument in argument.names
            ),
            None,
        )

    def _provided_option_values(self, app, extra_args: list[str]) -> dict[str, str]:
        values: dict[str, str] = {}
        index = 0
        while index < len(extra_args):
            token = extra_args[index]
            matched_argument = next(
                (
                    argument
                    for argument in app.arguments
                    if any(token == name or token.startswith(name + "=") for name in argument.names)
                ),
                None,
            )
            if matched_argument is None:
                index += 1
                continue
            if matched_argument.action in {"store_true", "store_false"}:
                values[matched_argument.primary_name] = "true"
                index += 1
                continue
            if "=" in token:
                values[matched_argument.primary_name] = token.split("=", 1)[1]
                index += 1
                continue
            if index + 1 < len(extra_args):
                values[matched_argument.primary_name] = extra_args[index + 1]
                index += 2
                continue
            index += 1
        return values

    def _provided_path_values(self, app, extra_args: list[str]) -> list[tuple[Any, str]]:
        option_values = self._provided_option_values(app, extra_args)
        return [
            (argument, option_values[argument.primary_name])
            for argument in app.arguments
            if argument.kind == "path" and argument.primary_name in option_values
        ]

    def _render_inline_content(self, content: Any) -> str:
        if isinstance(content, (dict, list)):
            return json.dumps(content, ensure_ascii=False, indent=2)
        if content is None:
            return ""
        return str(content)

    def _choose_inline_filename(self, argument_name: str, requested_filename: str | None, content: str) -> str:
        base_name = requested_filename or argument_name.lstrip("-").replace("-", "_")
        sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", base_name).strip("._") or "source"
        if "." in sanitized:
            return sanitized
        if self._looks_like_json(content):
            return f"{sanitized}.json"
        if self._looks_like_csv(content):
            return f"{sanitized}.csv"
        return f"{sanitized}.txt"

    def _default_output_filename(self, app, argument_name: str, extra_args: list[str]) -> str:
        format_value = self._provided_option_values(app, extra_args).get("--output-format", "").lower()
        extension_by_format = {
            "json": ".json",
            "csv": ".csv",
            "markdown": ".md",
            "md": ".md",
            "txt": ".txt",
            "text": ".txt",
        }
        extension = extension_by_format.get(format_value, ".txt")
        return f"{argument_name.lstrip('-').replace('-', '_')}{extension}"

    def _describe_artifact(self, path: Path, argument_name: str, preview_chars: int) -> dict[str, Any]:
        payload = {
            "argument": argument_name,
            "path": str(path),
            "exists": path.exists(),
        }
        if not path.exists():
            return payload

        payload["size_bytes"] = path.stat().st_size
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return payload

        payload["content_preview"] = self._trim_preview(content, preview_chars)
        if path.suffix.lower() == ".json" and len(content) <= preview_chars:
            try:
                payload["json_preview"] = json.loads(content)
            except json.JSONDecodeError:
                pass
        return payload

    def _metrics_path_for_process_run(self, app_id: str, run_id: str) -> Path:
        return (self.root_dir / ".sage" / "opc-runtime-metrics" / app_id / run_id / "metrics.json").resolve()

    def _read_metrics_artifact(self, path: Path | None) -> dict[str, Any] | None:
        if path is None or not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _wait_for_metrics_artifact(self, path: Path | None, *, timeout_seconds: float) -> dict[str, Any] | None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            metrics = self._read_metrics_artifact(path)
            if metrics is not None:
                return metrics
            time.sleep(0.1)
        return self._read_metrics_artifact(path)

    def _trim_preview(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return value[:limit] + "\n...<truncated>"

    def _looks_like_json(self, content: str) -> bool:
        stripped = content.strip()
        return stripped.startswith("{") or stripped.startswith("[")

    def _looks_like_csv(self, content: str) -> bool:
        lines = [line for line in content.splitlines() if line.strip()]
        return len(lines) >= 2 and "," in lines[0]

    def _is_port_available(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                return False
        return True

    def _format_command_preview(self, command: list[str], working_dir: Path, env: dict[str, str]) -> str:
        env_preview = []
        if env.get("PYTHONPATH"):
            env_preview.append(f"PYTHONPATH={shlex.quote(env['PYTHONPATH'])}")
        rendered_command = shlex.join(command)
        prefix = " ".join(env_preview)
        body = f"{prefix} {rendered_command}".strip()
        return f"cd {shlex.quote(str(working_dir))}\n{body}"

    def _start_pipe_reader(self, instance: RunningInstance, stream: str, pipe) -> None:
        if pipe is None:
            return

        def _consume() -> None:
            for raw_line in iter(pipe.readline, ""):
                line = raw_line.rstrip()
                if not line:
                    continue
                log = LogLine(timestamp=_now_iso(), stream=stream, message=line)
                with instance.lock:
                    instance.logs.append(log)
            pipe.close()

        thread = threading.Thread(target=_consume, daemon=True)
        thread.start()

    def _start_process_watcher(self, instance: RunningInstance) -> None:
        def _watch() -> None:
            if instance.process is None:
                return
            exit_code = instance.process.wait()
            with instance.lock:
                intentional_stop = instance.status in {"stopping", "stopped"}
                instance.exit_code = exit_code
                instance.ended_at = _now_iso()
                if intentional_stop:
                    instance.status = "stopped"
                elif instance.status not in {"stopped", "failed", "completed"}:
                    instance.status = "completed" if exit_code == 0 else "failed"
                if exit_code != 0 and instance.last_error is None and not intentional_stop:
                    instance.last_error = f"Process exited with code {exit_code}."
                if instance.metrics_path:
                    instance.metrics = self._read_metrics_artifact(Path(instance.metrics_path))
            self._record_event(
                instance,
                "process_exited",
                "Process exited.",
                {"exit_code": exit_code},
            )

        thread = threading.Thread(target=_watch, daemon=True)
        thread.start()

    def _wait_until_ready(self, instance: RunningInstance, *, timeout_seconds: float) -> bool:
        deadline = time.time() + timeout_seconds
        app = self.get_app_definition(instance.app_id)
        probe_path = app.health_path or app.start_probe_path
        if instance.port is None or probe_path is None:
            time.sleep(0.5)
            alive = instance.process is not None and instance.process.poll() is None
            if alive:
                with instance.lock:
                    instance.status = "running"
                return True
            return False

        while time.time() < deadline:
            if instance.process is not None and instance.process.poll() is not None:
                return False
            url = f"http://{instance.host}:{instance.port}{probe_path}"
            try:
                with httpx.Client(timeout=1.5, follow_redirects=True) as client:
                    response = client.get(url)
                if response.status_code < 400:
                    with instance.lock:
                        instance.status = "running"
                    return True
            except httpx.HTTPError:
                pass
            time.sleep(0.4)
        return False

    def _record_event(
        self,
        instance: RunningInstance,
        kind: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        with instance.lock:
            instance.events.append(
                LifecycleEvent(
                    timestamp=_now_iso(),
                    kind=kind,
                    message=message,
                    details=details or {},
                )
            )

    def _record_experiment(
        self,
        kind: str,
        status: str,
        summary: str,
        *,
        app_id: str | None = None,
        app_name: str | None = None,
        instance_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._experiment_records.append(
            ExperimentRecord(
                record_id=uuid.uuid4().hex[:10],
                timestamp=_now_iso(),
                kind=kind,
                status=status,
                summary=summary,
                app_id=app_id,
                app_name=app_name,
                instance_id=instance_id,
                details=details or {},
            )
        )

    def _http_check(
        self,
        name: str,
        url: str,
        *,
        method: str = "GET",
        json_payload: dict[str, Any] | None = None,
    ) -> CompatibilityTestResult:
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=3.0, follow_redirects=True) as client:
                response = client.request(method, url, json=json_payload)
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            status = "passed" if response.status_code < 400 else "failed"
            detail = f"{response.status_code} {response.reason_phrase}".strip()
        except httpx.HTTPError as exc:
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            status = "failed"
            detail = str(exc)
        return CompatibilityTestResult(
            name=name,
            status=status,
            latency_ms=latency_ms,
            last_run=_now_iso(),
            details=detail,
        )

    def _compatibility_overall(self, tests: list[CompatibilityTestResult]) -> str:
        statuses = {test.status for test in tests}
        if "failed" in statuses:
            return "failed"
        if statuses == {"skipped"}:
            return "skipped"
        if "passed" in statuses and "skipped" in statuses:
            return "partial"
        if "passed" in statuses:
            return "passed"
        return "unknown"

    def _get_service_instance_by_model(self, model_id: str) -> RunningInstance:
        for instance in self._instances.values():
            if instance.service_mode and (instance.openai_model == model_id or instance.instance_id == model_id):
                return instance
        raise KeyError(f"Unknown OpenAI model id: {model_id}")

    def _openai_messages_to_prompt(self, messages: list[Any]) -> str:
        if not messages:
            return ""
        texts = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            content = self._openai_message_content_to_text(message.get("content"))
            if not content:
                continue
            if message.get("role") == "user":
                texts.append(content)
        if texts:
            return "\n\n".join(texts)
        fallback = [
            self._openai_message_content_to_text(message.get("content"))
            for message in messages
            if isinstance(message, dict)
        ]
        return "\n\n".join(text for text in fallback if text)

    def _openai_message_content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text") or ""))
            return "\n".join(part for part in parts if part)
        if content is None:
            return ""
        return str(content)

    def _openai_payload_to_invoke_payload(self, payload: dict[str, Any], *, prompt_key: str, prompt_value: str) -> dict[str, Any]:
        invoke_payload: dict[str, Any] = {prompt_key: prompt_value}
        passthrough_keys = {
            "prompt_argument",
            "prompt_filename",
            "source_argument",
            "source_filename",
            "inline_files",
            "extra_args",
            "env",
            "timeout_seconds",
            "capture_output_preview_chars",
        }
        for key in passthrough_keys:
            if key in payload:
                invoke_payload[key] = payload[key]
        return invoke_payload

    def _openai_response_content(self, result: dict[str, Any]) -> str:
        for artifact in result.get("output_artifacts") or []:
            json_preview = artifact.get("json_preview")
            if json_preview is not None:
                return json.dumps(json_preview, ensure_ascii=False)
            preview = artifact.get("content_preview")
            if preview:
                return str(preview)
        if result.get("stdout"):
            return str(result["stdout"])
        if result.get("stderr"):
            return str(result["stderr"])
        return ""

    def _openai_usage(self, prompt: str, completion: str) -> dict[str, int]:
        prompt_tokens = self._rough_token_count(prompt)
        completion_tokens = self._rough_token_count(completion)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def _rough_token_count(self, text: str) -> int:
        normalized = text.strip()
        if not normalized:
            return 0
        return max(len(normalized.split()), 1)