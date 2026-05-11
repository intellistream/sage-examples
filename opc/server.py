"""FastAPI server for the SAGE OPC web console."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .runtime import ProcessRuntimeAdapter


STATIC_DIR = Path(__file__).resolve().parent / "static"


class LaunchRequest(BaseModel):
    host: str = "127.0.0.1"
    port: int | None = None
    auto_port: bool = True
    storage_path: str | None = None
    extra_args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    allow_duplicate: bool = False
    service_mode: bool = False
    startup_timeout_seconds: float = 12.0


class InlineFileRequest(BaseModel):
    argument: str | None = None
    content: Any
    filename: str | None = None


class InvokeRequest(BaseModel):
    source: Any | None = None
    source_argument: str | None = None
    source_filename: str | None = None
    prompt: Any | None = None
    prompt_argument: str | None = None
    prompt_filename: str | None = None
    inline_files: list[InlineFileRequest] = Field(default_factory=list)
    extra_args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = 30.0
    capture_output_preview_chars: int = 12000


def create_app(
    *,
    root_dir: str | Path | None = None,
    python_executable: str | None = None,
    port_range_start: int = 18000,
    port_range_end: int = 18100,
) -> FastAPI:
    resolved_root = Path(root_dir or Path(__file__).resolve().parents[1]).resolve()
    runtime = ProcessRuntimeAdapter(
        resolved_root,
        python_executable=python_executable or sys.executable,
        port_range_start=port_range_start,
        port_range_end=port_range_end,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        runtime.stop_all()

    app = FastAPI(title="SAGE OPC", version="0.1.0", lifespan=lifespan)
    app.state.runtime = runtime

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/api/health")
    def api_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/models")
    def openai_models() -> dict[str, Any]:
        return runtime.list_openai_models()

    @app.post("/v1/chat/completions")
    def openai_chat_completions(request: dict[str, Any]) -> dict[str, Any]:
        try:
            return runtime.openai_chat_completion(request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/completions")
    def openai_completions(request: dict[str, Any]) -> dict[str, Any]:
        try:
            return runtime.openai_completion(request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/apps")
    def list_apps() -> dict[str, Any]:
        return {"apps": runtime.discover_apps()}

    @app.get("/api/apps/{app_id}")
    def get_app(app_id: str) -> dict[str, Any]:
        try:
            return runtime.get_app_definition(app_id).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/apps/{app_id}/validate")
    def validate_launch(app_id: str, request: LaunchRequest) -> dict[str, Any]:
        try:
            return runtime.validate_launch_config(app_id, request.model_dump())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/apps/{app_id}/launch")
    def launch_app(app_id: str, request: LaunchRequest) -> dict[str, Any]:
        try:
            return runtime.launch_app(app_id, request.model_dump())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/apps/{app_id}/invoke")
    def invoke_app(app_id: str, request: InvokeRequest) -> dict[str, Any]:
        try:
            return runtime.invoke_app(app_id, request.model_dump())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/instances")
    def list_instances() -> dict[str, Any]:
        return {"instances": runtime.list_instances()}

    @app.get("/api/instances/{instance_id}")
    def get_instance(instance_id: str) -> dict[str, Any]:
        try:
            return runtime.get_instance(instance_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/instances/{instance_id}/invoke")
    def invoke_instance(instance_id: str, request: InvokeRequest) -> dict[str, Any]:
        try:
            return runtime.invoke_instance(instance_id, request.model_dump())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/instances/{instance_id}/logs")
    def get_logs(
        instance_id: str,
        stream: str = Query("merged", pattern="^(merged|stdout|stderr)$"),
        limit: int = Query(200, ge=1, le=2000),
        query: str | None = None,
    ) -> dict[str, Any]:
        try:
            return runtime.get_logs(instance_id, stream=stream, limit=limit, query=query)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/instances/{instance_id}/stop")
    def stop_instance(instance_id: str) -> dict[str, Any]:
        try:
            return runtime.stop_app(instance_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/instances/{instance_id}/restart")
    def restart_instance(instance_id: str) -> dict[str, Any]:
        try:
            return runtime.restart_app(instance_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/instances/{instance_id}/compatibility")
    def run_compatibility(instance_id: str) -> dict[str, Any]:
        try:
            return runtime.run_compatibility_check(instance_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/instances/{instance_id}/demo-run")
    def run_demo(instance_id: str) -> dict[str, Any]:
        try:
            return runtime.run_instance_demo(instance_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/ports")
    def ports() -> dict[str, Any]:
        return runtime.list_ports()

    @app.get("/api/settings")
    def settings() -> dict[str, Any]:
        return runtime.settings()

    @app.get("/api/experiments")
    def experiments() -> dict[str, Any]:
        return runtime.list_experiments()

    @app.post("/api/experiments/reset")
    def reset_experiments() -> dict[str, Any]:
        return runtime.reset_experiments()

    @app.get("/api/reports/inventory")
    def inventory_report() -> PlainTextResponse:
        return PlainTextResponse(runtime.export_inventory_markdown())

    @app.get("/api/reports/compatibility")
    def compatibility_report() -> PlainTextResponse:
        return PlainTextResponse(runtime.export_compatibility_markdown())

    @app.get("/api/reports/experiments")
    def experiments_report() -> PlainTextResponse:
        return PlainTextResponse(runtime.export_experiments_json(), media_type="application/json")

    @app.get("/", response_class=HTMLResponse)
    def root():
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse("<h1>SAGE OPC</h1><p>Frontend assets not found.</p>")

    return app