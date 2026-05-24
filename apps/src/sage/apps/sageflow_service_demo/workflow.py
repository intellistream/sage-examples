"""Workflow runner that wires a SageFlow-style service into a SAGE environment."""

from __future__ import annotations

from sage.runtime import BaseService, LocalEnvironment

from .adapter import InMemorySageFlowSnapshotAdapter
from .models import LLMGenerationResult, SageFlowWindowSnapshot, SnapshotContract, VectorSnapshotInsight, VectorStreamEvent
from .operators import (
    BuildSnapshotContractStep,
    DeriveOperationalInsightStep,
    DemoVectorEventSource,
    EmbedTextSignalStep,
    GenerateLLMAnswerStep,
    InsightCollectorSink,
    NormalizeVectorEventStep,
    QuerySageFlowWindowJoinStep,
    RealEmbeddingStep,
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
        *,
        use_real_embeddings: bool = False,
        generate_llm: bool = False,
        allow_template_fallback: bool = False,
    ) -> tuple[list[VectorSnapshotInsight], list[SnapshotContract], list[LLMGenerationResult]]:
        insights: list[VectorSnapshotInsight] = []
        contracts: list[SnapshotContract] = []
        answers: list[LLMGenerationResult] = []
        environment = self._build_environment("sageflow_service_demo_ingest")
        embedding_step = RealEmbeddingStep if use_real_embeddings else EmbedTextSignalStep
        stream = (
            environment.from_batch(DemoVectorEventSource, events=events)
            .map(embedding_step)
            .map(NormalizeVectorEventStep)
            .map(QuerySageFlowWindowJoinStep)
            .map(DeriveOperationalInsightStep)
            .map(BuildSnapshotContractStep)
        )
        if generate_llm:
            stream = stream.map(GenerateLLMAnswerStep, allow_template_fallback=allow_template_fallback)
        stream.sink(InsightCollectorSink, results=insights, contracts=contracts, answers=answers)
        environment.submit(autostop=True)
        return insights, contracts, answers

    def get_latest_snapshot(self) -> SageFlowWindowSnapshot | None:
        return self.adapter.get_latest_snapshot()
