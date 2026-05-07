"""Models for the SageFlow-as-a-service demo application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


def _to_payload(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_payload(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class VectorStreamEvent:
    event_id: str
    source: str
    timestamp: str
    summary: str
    embedding: tuple[float, ...]
    severity: float
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source": self.source,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "embedding": list(self.embedding),
            "severity": self.severity,
            "tags": list(self.tags),
            "metadata": _to_payload(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VectorStreamEvent":
        embedding = payload.get("embedding")
        if not isinstance(embedding, (list, tuple)) or not embedding:
            raise ValueError("embedding must be a non-empty list or tuple of numbers")

        return cls(
            event_id=str(payload["event_id"]),
            source=str(payload["source"]),
            timestamp=str(payload["timestamp"]),
            summary=str(payload["summary"]),
            embedding=tuple(float(item) for item in embedding),
            severity=float(payload.get("severity", 0.0)),
            tags=tuple(str(item) for item in payload.get("tags", ())),
            metadata=dict(payload.get("metadata", {})),
        )


def coerce_vector_stream_event(value: VectorStreamEvent | dict[str, Any]) -> VectorStreamEvent:
    if isinstance(value, VectorStreamEvent):
        return value
    if isinstance(value, dict):
        return VectorStreamEvent.from_dict(value)
    raise TypeError(f"Unsupported vector event type: {type(value)!r}")


@dataclass(frozen=True)
class NearestNeighbor:
    event_id: str
    source: str
    similarity: float
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClusterSnapshot:
    cluster_id: str
    size: int
    average_severity: float
    member_ids: list[str]
    top_tags: list[str]
    source_breakdown: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SageFlowWindowSnapshot:
    generated_at: str
    window_size: int
    cluster_count: int
    latest_event_id: str
    hot_clusters: list[ClusterSnapshot]
    source_breakdown: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return _to_payload(asdict(self))


@dataclass(frozen=True)
class SageFlowServiceResponse:
    event: VectorStreamEvent
    active_cluster: ClusterSnapshot
    novelty_score: float
    nearest_neighbors: list[NearestNeighbor]
    window_snapshot: SageFlowWindowSnapshot

    def to_dict(self) -> dict[str, Any]:
        return _to_payload(asdict(self))


@dataclass(frozen=True)
class SageFlowRuntimeInfo:
    mode: str
    join_method: str
    similarity_threshold: float
    window_size_ms: int
    parallelism: int
    retained_left_records: int
    retained_right_records: int
    queued_left_records: int
    queued_right_records: int
    emitted_pairs: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VectorSnapshotInsight:
    insight_id: str
    insight_type: str
    title: str
    summary: str
    severity: str
    related_event_id: str
    related_cluster_id: str | None = None
    supporting_neighbor_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TriageRouteDecision:
    event_id: str
    route: str
    priority: str
    focus_sources: list[str]
    supporting_neighbor_ids: list[str]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SecurityEscalationSignal:
    event_id: str
    action: str
    severity: str
    supporting_neighbor_ids: list[str]
    related_cluster_id: str | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["corroborating_neighbor_ids"] = list(self.supporting_neighbor_ids)
        return payload


@dataclass(frozen=True)
class InsightEnvelope:
    response: SageFlowServiceResponse
    insights: list[VectorSnapshotInsight]


@dataclass(frozen=True)
class SageFlowDemoRunResult:
    processed_event_count: int
    insight_count: int
    insights: list[VectorSnapshotInsight]
    final_snapshot: SageFlowWindowSnapshot | None

    def to_dict(self) -> dict[str, Any]:
        return _to_payload(asdict(self))
