"""Workflow operators for the SageFlow service integration demo."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from sage.foundation import BatchFunction, MapFunction, SinkFunction

from .models import (
    InsightEnvelope,
    LLMGenerationResult,
    SageFlowServiceResponse,
    SnapshotContract,
    VectorSnapshotInsight,
    VectorStreamEvent,
    coerce_vector_stream_event,
)
from .contracts import build_snapshot_contract
from .embeddings import create_embedding_client_from_env, event_text, load_cache_from_env
from .llm import generate_answer_from_contract

SAGEFLOW_SERVICE_NAME = "sageflow_vector_snapshot"


class DemoVectorEventSource(BatchFunction):
    def __init__(self, events: list[Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self.events = list(events)
        self.index = 0

    def execute(self) -> Any | None:
        if self.index >= len(self.events):
            return None
        event = self.events[self.index]
        self.index += 1
        return event


class NormalizeVectorEventStep(MapFunction):
    def execute(self, data: VectorStreamEvent | dict[str, Any]) -> VectorStreamEvent:
        return coerce_vector_stream_event(data)


class EmbedTextSignalStep(MapFunction):
    """Deterministically embed raw vulnerability records for reproducible replay."""

    def execute(self, data: VectorStreamEvent | dict[str, Any]) -> VectorStreamEvent:
        if isinstance(data, VectorStreamEvent):
            return data
        if "embedding" in data:
            return coerce_vector_stream_event(data)
        payload = dict(data)
        payload["embedding"] = _embed_payload(payload)
        return coerce_vector_stream_event(payload)


class RealEmbeddingStep(MapFunction):
    """Attach real cached/service embeddings to raw records.

    This step is the paper/demo path. `EmbedTextSignalStep` remains available
    only for deterministic unit fixtures.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cache = load_cache_from_env()
        self.client = create_embedding_client_from_env()

    def execute(self, data: VectorStreamEvent | dict[str, Any]) -> VectorStreamEvent:
        if isinstance(data, VectorStreamEvent):
            return data
        if "embedding" in data:
            return coerce_vector_stream_event(data)

        event_id = str(data.get("event_id", ""))
        embedding = self.cache.get(event_id) if self.cache is not None else None
        if embedding is None and self.client is not None:
            embedding = self.client.embed(event_text(data))
        if embedding is None:
            raise ValueError(
                "RealEmbeddingStep requires either an embedding field, "
                "SAGEFLOW_DEMO_EMBEDDING_CACHE, or an embedding service configuration."
            )

        payload = dict(data)
        payload["embedding"] = embedding
        metadata = dict(payload.get("metadata", {}))
        if self.cache is not None:
            metadata["embedding_cache"] = str(self.cache.path)
            metadata["embedding_cache_metadata"] = self.cache.metadata
        payload["metadata"] = metadata
        return coerce_vector_stream_event(payload)


class QuerySageFlowWindowJoinStep(MapFunction):
    def execute(self, data: VectorStreamEvent) -> SageFlowServiceResponse:
        return self.call_service(SAGEFLOW_SERVICE_NAME, data, method="process_event")


class DeriveOperationalInsightStep(MapFunction):
    def execute(self, data: SageFlowServiceResponse) -> InsightEnvelope:
        insights: list[VectorSnapshotInsight] = []
        cluster = data.active_cluster
        neighbor_ids = [item.event_id for item in data.nearest_neighbors]

        if (
            cluster.size >= 3
            and cluster.average_severity >= 0.70
            and len(cluster.source_breakdown) >= 2
        ):
            insights.append(
                VectorSnapshotInsight(
                    insight_id=f"correlated-{data.event.event_id}",
                    insight_type="correlated_incident",
                    title="Window runtime detected a cross-source evidence cluster",
                    summary=(
                        f"{cluster.cluster_id} 已聚合 {cluster.size} 条相似事件，来源覆盖 "
                        f"{', '.join(sorted(cluster.source_breakdown))}，适合直接作为 upper layer 的中间"
                        "快照输入给后续诊断或生成式解释节点。"
                    ),
                    severity="high",
                    related_event_id=data.event.event_id,
                    related_cluster_id=cluster.cluster_id,
                    supporting_neighbor_ids=neighbor_ids,
                )
            )

        if data.novelty_score >= 0.18 and data.event.severity >= 0.95:
            insights.append(
                VectorSnapshotInsight(
                    insight_id=f"emerging-{data.event.event_id}",
                    insight_type="emerging_pattern",
                    title="Window runtime surfaced a high-risk vector pattern",
                    summary=(
                        f"事件 {data.event.event_id} 的新颖度为 {data.novelty_score:.2f}，尚未被现有"
                        "热点簇吸收，适合触发 upper layer 的优先级升级、告警编排或 LLM 解释。"
                    ),
                    severity="critical",
                    related_event_id=data.event.event_id,
                    related_cluster_id=cluster.cluster_id,
                    supporting_neighbor_ids=neighbor_ids,
                )
            )

        return InsightEnvelope(response=data, insights=insights)


class BuildSnapshotContractStep(MapFunction):
    def execute(self, data: InsightEnvelope | SageFlowServiceResponse) -> InsightEnvelope:
        if isinstance(data, InsightEnvelope):
            return InsightEnvelope(
                response=data.response,
                insights=data.insights,
                contract=build_snapshot_contract(data.response),
                llm_answer=data.llm_answer,
            )
        return InsightEnvelope(response=data, insights=[], contract=build_snapshot_contract(data))


class GenerateLLMAnswerStep(MapFunction):
    def __init__(self, *, allow_template_fallback: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.allow_template_fallback = allow_template_fallback

    def execute(self, data: InsightEnvelope) -> InsightEnvelope:
        if data.contract is None:
            raise ValueError("GenerateLLMAnswerStep requires a snapshot contract")
        answer = generate_answer_from_contract(
            data.contract,
            allow_template_fallback=self.allow_template_fallback,
        )
        return InsightEnvelope(
            response=data.response,
            insights=data.insights,
            contract=data.contract,
            llm_answer=answer,
        )


class InsightCollectorSink(SinkFunction):
    def __init__(
        self,
        results: list[VectorSnapshotInsight],
        contracts: list[SnapshotContract] | None = None,
        answers: list[LLMGenerationResult] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.results = results
        self.contracts = contracts
        self.answers = answers

    def execute(self, data: InsightEnvelope) -> None:
        self.results.extend(data.insights)
        if self.contracts is not None and data.contract is not None:
            self.contracts.append(data.contract)
        if self.answers is not None and data.llm_answer is not None:
            self.answers.append(data.llm_answer)


def _embed_payload(payload: dict[str, Any]) -> list[float]:
    vector = [0.0] * 16
    tags = [str(item).lower() for item in payload.get("tags", [])]
    summary = str(payload.get("summary", "")).lower()
    text = " ".join([summary, *tags])
    for axis, terms in enumerate(
        [
            ("cve-2024-3400", "pan-os", "globalprotect"),
            ("cve-2024-3094", "xz-utils", "liblzma"),
            ("cve-2024-6387", "openssh", "regresshion"),
            ("cve-2024-4577", "php-cgi", "php"),
            ("cve-2024-21762", "fortios", "fortiproxy"),
            ("cve-2024-27198", "teamcity", "ci-cd"),
        ]
    ):
        if any(term in text for term in terms):
            vector[axis] = 1.0
            break
    else:
        vector[7] = 1.0

    source_hash = int(hashlib.sha1(str(payload.get("source", "")).encode("utf-8")).hexdigest()[:8], 16)
    vector[8 + source_hash % 4] = 0.025
    vector[12] = float(payload.get("severity", 0.0)) * 0.02
    vector[15] = 0.01
    norm = math.sqrt(sum(item * item for item in vector))
    return [round(item / norm, 6) for item in vector]
