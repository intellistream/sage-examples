"""SAGE workflow orchestration for the ticket triage MVP."""

from __future__ import annotations

from pathlib import Path

from sage.runtime import BaseService, LocalEnvironment

from .models import TicketEvent, TicketStatusSnapshot, TicketTriageResult
from .operators import (
    ClassifyIntentStep,
    DecideRouteStep,
    DemoTicketSource,
    DraftReplyStep,
    EnrichCustomerContextStep,
    NormalizeTicketStep,
    PersistTicketStateStep,
    RecallSimilarCasesStep,
    ResultCollectorSink,
    STATE_SERVICE_NAME,
    ScoreUrgencyStep,
)
from .state_store import InMemoryTicketTriageStateStore


class TicketTriageStateService(BaseService):
    """Runtime service exposing explicit state operations to workflow nodes."""

    def __init__(self, store: InMemoryTicketTriageStateStore) -> None:
        super().__init__()
        self.store = store

    def load_reference_data(self, knowledge_articles, historical_resolutions) -> None:
        self.store.load_reference_data(knowledge_articles, historical_resolutions)

    def save_ticket_snapshot(self, snapshot) -> None:
        self.store.save_ticket_snapshot(snapshot)

    def get_ticket_snapshot(self, ticket_id: str):
        return self.store.get_ticket_snapshot(ticket_id)

    def build_status_snapshot(self, ticket_id: str):
        return self.store.build_status_snapshot(ticket_id)

    def list_customer_recent_tickets(self, customer_id: str):
        return self.store.list_customer_recent_tickets(customer_id)

    def search_knowledge_articles(self, intent: str, normalized_text: str):
        return self.store.search_knowledge_articles(intent, normalized_text)

    def search_similar_resolutions(self, intent: str, normalized_text: str):
        return self.store.search_similar_resolutions(intent, normalized_text)

    def append_triage_result(self, result) -> None:
        self.store.append_triage_result(result)

    def assign_team_queue(self, result) -> None:
        self.store.assign_team_queue(result)

    def list_queue_summary(self):
        return self.store.list_queue_summary()

    def list_open_high_priority_tickets(self):
        return self.store.list_open_high_priority_tickets()


class TicketTriageWorkflowRunner:
    """Thin workflow runner that rebuilds a LocalEnvironment per ingest operation."""

    def __init__(self, state_store: InMemoryTicketTriageStateStore | None = None) -> None:
        self.state_store = state_store or InMemoryTicketTriageStateStore()

    @classmethod
    def from_storage_path(cls, storage_path: str | Path | None = None) -> TicketTriageWorkflowRunner:
        return cls(InMemoryTicketTriageStateStore(storage_path=storage_path))

    def _build_environment(self, name: str) -> LocalEnvironment:
        environment = LocalEnvironment(name)
        environment.set_console_log_level("ERROR")
        environment.register_service(STATE_SERVICE_NAME, TicketTriageStateService, self.state_store)
        return environment

    def ingest_tickets(self, events: list[TicketEvent | dict]) -> list[TicketTriageResult]:
        results: list[TicketTriageResult] = []
        environment = self._build_environment("ticket_triage_ingest")
        (
            environment.from_batch(DemoTicketSource, events=events)
            .map(NormalizeTicketStep)
            .map(EnrichCustomerContextStep)
            .map(ClassifyIntentStep)
            .map(ScoreUrgencyStep)
            .map(RecallSimilarCasesStep)
            .map(DecideRouteStep)
            .map(DraftReplyStep)
            .map(PersistTicketStateStep)
            .sink(ResultCollectorSink, results=results)
        )
        environment.submit(autostop=True)
        return results

    def get_ticket(self, ticket_id: str) -> TicketStatusSnapshot | None:
        return self.state_store.get_ticket_snapshot(ticket_id)