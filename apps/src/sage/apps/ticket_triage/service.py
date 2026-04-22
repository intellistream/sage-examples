"""Service facade and optional FastAPI adapter for the ticket triage MVP."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
except ImportError:  # pragma: no cover - optional dependency for HTTP adapter only
    FastAPI = None
    HTTPException = None
    HTMLResponse = None

from .demo_data import (
    build_demo_historical_resolutions,
    build_demo_knowledge_articles,
    build_demo_summary,
    build_demo_tickets,
)
from .models import TicketEvent, TicketStatusSnapshot, TicketTriageRunResult, coerce_ticket_event
from .state_store import InMemoryTicketTriageStateStore
from .ui import render_dashboard_page
from .workflow import TicketTriageWorkflowRunner


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


class TicketTriageApplicationService:
    """High-level service interface for demo ingest and queue queries."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.state_store = InMemoryTicketTriageStateStore(storage_path=storage_path)
        self.workflow = TicketTriageWorkflowRunner(self.state_store)
        self._ensure_reference_data()

    def _ensure_reference_data(self, *, force: bool = False) -> None:
        if force or not self.state_store.has_reference_data():
            self.state_store.load_reference_data(
                build_demo_knowledge_articles(),
                build_demo_historical_resolutions(),
            )

    def reset(self) -> None:
        self.state_store.reset()
        self._ensure_reference_data(force=True)

    def ingest_tickets(self, events: list[TicketEvent | dict[str, Any]]) -> TicketTriageRunResult:
        self._ensure_reference_data()
        resolved_events = [coerce_ticket_event(item) for item in events]
        triage_results = self.workflow.ingest_tickets(resolved_events)
        queue_summaries = self.state_store.list_queue_summary()
        high_priority_count = sum(
            1 for item in triage_results if item.priority in {"high", "critical"}
        )
        return TicketTriageRunResult(
            processed_event_count=len(resolved_events),
            high_priority_count=high_priority_count,
            triage_results=triage_results,
            queue_summaries=queue_summaries,
        )

    def run_demo(self, *, reset: bool = True) -> TicketTriageRunResult:
        if reset:
            self.reset()
        return self.ingest_tickets(build_demo_tickets())

    def get_ticket(self, ticket_id: str) -> TicketStatusSnapshot:
        snapshot = self.state_store.get_ticket_snapshot(ticket_id)
        if snapshot is None:
            raise KeyError(f"No ticket found for '{ticket_id}'.")
        return snapshot

    def list_queue_summary(self):
        return self.state_store.list_queue_summary()

    def list_open_high_priority_tickets(self):
        return self.state_store.list_open_high_priority_tickets()

    def list_triage_results(self):
        return self.state_store.list_triage_results()

    def get_dashboard_summary(self) -> dict[str, Any]:
        triage_results = self.list_triage_results()
        queue_summaries = self.list_queue_summary()
        high_priority_count = sum(
            1 for item in triage_results if item.priority in {"high", "critical"}
        )
        auto_reply_count = sum(1 for item in triage_results if item.auto_reply)
        escalated_count = sum(
            1
            for item in triage_results
            if item.assigned_team == "duty_manager"
            or item.recommended_action == "supervisor_escalation"
        )
        intent_distribution: dict[str, int] = {}
        for item in triage_results:
            intent_distribution[item.intent] = intent_distribution.get(item.intent, 0) + 1
        busiest_queue = queue_summaries[0].team_name if queue_summaries else None
        latest_ticket_id = triage_results[0].ticket_id if triage_results else None
        return {
            "total_ticket_count": len(triage_results),
            "high_priority_count": high_priority_count,
            "auto_reply_count": auto_reply_count,
            "escalated_count": escalated_count,
            "queue_count": len(queue_summaries),
            "busiest_queue": busiest_queue,
            "latest_ticket_id": latest_ticket_id,
            "intent_distribution": intent_distribution,
        }

    def get_demo_summary(self) -> dict[str, int]:
        return build_demo_summary()


def create_demo_application_service(
    storage_path: str | Path | None = None,
) -> TicketTriageApplicationService:
    return TicketTriageApplicationService(storage_path=storage_path)


def create_fastapi_app(
    service: TicketTriageApplicationService | None = None,
) -> FastAPI:
    if FastAPI is None or HTTPException is None or HTMLResponse is None:
        raise RuntimeError(
            "FastAPI is not installed. Install fastapi to use the ticket triage API."
        )

    runtime_service = service or TicketTriageApplicationService()
    app = FastAPI(title="SAGE Ticket Triage MVP", version="0.1.0")

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "name": "SAGE Ticket Triage MVP",
            "version": "0.1.0",
            "routes": [
                "/docs",
                "/redoc",
                "/openapi.json",
                "/health",
                "/dashboard",
                "/dashboard/ui",
                "/tickets",
                "/tickets/ingest",
                "/tickets/high-priority",
                "/tickets/{ticket_id}",
                "/queues",
                "/demo/reset-and-run",
            ],
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/dashboard")
    def get_dashboard() -> dict[str, Any]:
        return _to_payload(runtime_service.get_dashboard_summary())

    @app.get("/dashboard/ui", response_class=HTMLResponse)
    def get_dashboard_ui() -> HTMLResponse:
        return HTMLResponse(render_dashboard_page())

    @app.get("/tickets")
    def list_tickets() -> list[dict[str, Any]]:
        return _to_payload(runtime_service.list_triage_results())

    @app.post("/tickets/ingest")
    def ingest_tickets(payload: list[dict[str, Any]]) -> dict[str, Any]:
        return _to_payload(runtime_service.ingest_tickets(payload))

    @app.get("/tickets/high-priority")
    def list_high_priority_tickets() -> list[dict[str, Any]]:
        return _to_payload(runtime_service.list_open_high_priority_tickets())

    @app.get("/tickets/{ticket_id}")
    def get_ticket(ticket_id: str) -> dict[str, Any]:
        try:
            return _to_payload(runtime_service.get_ticket(ticket_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/queues")
    def list_queue_summary() -> list[dict[str, Any]]:
        return _to_payload(runtime_service.list_queue_summary())

    @app.post("/demo/reset-and-run")
    def run_demo() -> dict[str, Any]:
        return _to_payload(runtime_service.run_demo(reset=True))

    return app
