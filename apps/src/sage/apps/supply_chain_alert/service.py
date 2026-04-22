"""Service facade and optional FastAPI adapter for the supply chain alert MVP."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
except ImportError:  # pragma: no cover - optional dependency for HTTP adapter only
    FastAPI = None
    HTMLResponse = None

from .demo_data import build_demo_event_summary, build_demo_supply_events
from .llm import SupplyChainRiskExplainer
from .models import (
    DashboardSnapshot,
    RiskExplanationResult,
    SupplyChainRunResult,
    SupplyEvent,
    coerce_supply_event,
)
from .ui import render_dashboard_page
from .workflow import SupplyChainWorkflowRunner


def _to_payload(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_payload(item) for key, item in value.items()}
    return value


def _resolve_last_timestamp(events: list[SupplyEvent]) -> str | None:
    if not events:
        return None
    timestamps = []
    for event in events:
        if hasattr(event, "observed_at"):
            timestamps.append(event.observed_at)
        elif hasattr(event, "updated_at"):
            timestamps.append(event.updated_at)
        elif hasattr(event, "recorded_at"):
            timestamps.append(event.recorded_at)
    return max(timestamps) if timestamps else None


class SupplyChainAlertApplicationService:
    """High-level service interface for demo ingest and dashboard queries."""

    def __init__(
        self,
        storage_path: str | Path | None = None,
        risk_explainer: SupplyChainRiskExplainer | None = None,
    ) -> None:
        self.workflow = SupplyChainWorkflowRunner.from_storage_path(storage_path=storage_path)
        self._risk_explainer = risk_explainer

    def reset(self) -> None:
        self.workflow.reset()

    def ingest_events(self, events: list[SupplyEvent | dict[str, Any]]) -> SupplyChainRunResult:
        resolved_events = [coerce_supply_event(item) for item in events]
        alerts = self.workflow.ingest_events(resolved_events)
        dashboard = self.workflow.get_dashboard(as_of=_resolve_last_timestamp(resolved_events))
        supplier_risk_summaries = self.workflow.list_supplier_risk_summary(limit=5)
        return SupplyChainRunResult(
            processed_event_count=len(resolved_events),
            alert_count=len(alerts),
            alerts=alerts,
            dashboard=dashboard,
            supplier_risk_summaries=supplier_risk_summaries,
        )

    def run_demo(self, *, reset: bool = True) -> SupplyChainRunResult:
        if reset:
            self.reset()
        return self.ingest_events(build_demo_supply_events())

    def get_dashboard(self) -> DashboardSnapshot:
        return self.workflow.get_dashboard()

    def list_open_alerts(self):
        return self.workflow.list_open_alerts()

    def get_supplier_risk_summary(self):
        return self.workflow.list_supplier_risk_summary(limit=5)

    def explain_current_risks(self, *, max_alerts: int = 5) -> RiskExplanationResult:
        explainer = self._risk_explainer or SupplyChainRiskExplainer()
        self._risk_explainer = explainer
        return explainer.explain_current_risks(
            dashboard=self.get_dashboard(),
            alerts=self.list_open_alerts(),
            supplier_risk_summaries=self.get_supplier_risk_summary(),
            max_alerts=max_alerts,
        )

    def get_demo_summary(self) -> dict[str, int]:
        return build_demo_event_summary()


def create_demo_application_service(
    storage_path: str | Path | None = None,
) -> SupplyChainAlertApplicationService:
    return SupplyChainAlertApplicationService(storage_path=storage_path)


def create_fastapi_app(
    service: SupplyChainAlertApplicationService | None = None,
) -> FastAPI:
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed. Install fastapi to use the supply chain HTTP adapter.",
        )

    runtime_service = service or SupplyChainAlertApplicationService()
    app = FastAPI(title="SAGE Supply Chain Alert Dashboard", version="0.1.0")

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "name": "SAGE Supply Chain Alert Dashboard",
            "version": "0.1.0",
            "routes": [
                "/health",
                "/dashboard",
                "/dashboard/ui",
                "/alerts/open",
                "/alerts/explanations",
                "/suppliers/risk",
                "/events/ingest",
                "/demo/reset-and-run",
            ],
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/events/ingest")
    def ingest_events(payload: list[dict[str, Any]]) -> dict[str, Any]:
        result = runtime_service.ingest_events(payload)
        return _to_payload(result)

    @app.get("/dashboard")
    def get_dashboard() -> dict[str, Any]:
        return _to_payload(runtime_service.get_dashboard())

    @app.get("/dashboard/ui", response_class=HTMLResponse)
    def get_dashboard_ui() -> HTMLResponse:
        return HTMLResponse(render_dashboard_page())

    @app.get("/alerts/open")
    def list_open_alerts() -> list[dict[str, Any]]:
        return _to_payload(runtime_service.list_open_alerts())

    @app.get("/alerts/explanations")
    def explain_current_risks(max_alerts: int = 5) -> dict[str, Any]:
        return _to_payload(runtime_service.explain_current_risks(max_alerts=max_alerts))

    @app.get("/suppliers/risk")
    def get_supplier_risk_summary() -> list[dict[str, Any]]:
        return _to_payload(runtime_service.get_supplier_risk_summary())

    @app.post("/demo/reset-and-run")
    def run_demo() -> dict[str, Any]:
        return _to_payload(runtime_service.run_demo(reset=True))

    return app
