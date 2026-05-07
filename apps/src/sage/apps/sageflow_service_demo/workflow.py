"""Workflow runner that wires a SageFlow-style service into a SAGE environment."""

from __future__ import annotations

from sage.runtime import BaseService, LocalEnvironment

from .adapter import InMemorySageFlowSnapshotAdapter
from .models import SageFlowWindowSnapshot, VectorSnapshotInsight, VectorStreamEvent
from .operators import (
    DeriveOperationalInsightStep,
    DemoVectorEventSource,
    EmbedTextSignalStep,
    InsightCollectorSink,
    NormalizeVectorEventStep,
    QuerySageFlowWindowJoinStep,
    SAGEFLOW_SERVICE_NAME,
)


class SageFlowSnapshotService(BaseService):
    """Runtime-local wrapper around a long-lived SageFlow adapter/client."""

    def __init__(self, adapter: InMemorySageFlowSnapshotAdapter) -> None:
        super().__init__()
        self.adapter = adapter

    def reset(self) -> None:
        self.adapter.reset()

    def process_event(self, event):
        return self.adapter.process_event(event)

    def get_latest_snapshot(self) -> SageFlowWindowSnapshot | None:
        return self.adapter.get_latest_snapshot()

    def cleanup(self) -> None:
        self.adapter.close()


class SageFlowServiceWorkflowRunner:
    def __init__(
        self,
        adapter: InMemorySageFlowSnapshotAdapter | None = None,
    ) -> None:
        self.adapter = adapter or InMemorySageFlowSnapshotAdapter()

    def _build_environment(self, name: str) -> LocalEnvironment:
        environment = LocalEnvironment(name)
        environment.set_console_log_level("ERROR")
        environment.register_service(SAGEFLOW_SERVICE_NAME, SageFlowSnapshotService, self.adapter)
        return environment

    def reset(self) -> None:
        self.adapter.reset()

    def ingest_events(
        self,
        events: list[VectorStreamEvent | dict],
    ) -> list[VectorSnapshotInsight]:
        insights: list[VectorSnapshotInsight] = []
        environment = self._build_environment("sageflow_service_demo_ingest")
        (
            environment.from_batch(DemoVectorEventSource, events=events)
            .map(EmbedTextSignalStep)
            .map(NormalizeVectorEventStep)
            .map(QuerySageFlowWindowJoinStep)
            .map(DeriveOperationalInsightStep)
            .sink(InsightCollectorSink, results=insights)
        )
        environment.submit(autostop=True)
        return insights

    def get_latest_snapshot(self) -> SageFlowWindowSnapshot | None:
        return self.adapter.get_latest_snapshot()
