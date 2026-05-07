"""High-level application services for the SageFlow ICPP demo."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from .adapter import InMemorySageFlowSnapshotAdapter
from .demo_data import (
    build_demo_summary,
    build_demo_vector_events,
    build_security_demo_vector_events,
)
from .models import (
    SageFlowDemoRunResult,
    SageFlowWindowSnapshot,
    SecurityEscalationSignal,
    TriageRouteDecision,
    VectorStreamEvent,
    coerce_vector_stream_event,
)
from .workflow import SageFlowServiceWorkflowRunner


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


class SageFlowServiceDemoApplication:
    """Snapshot-contract demo: SAGE calls a persistent SageFlow join service."""

    def __init__(
        self,
        *,
        window_size: int = 16,
        similarity_threshold: float = 0.985,
    ) -> None:
        adapter = InMemorySageFlowSnapshotAdapter(
            window_size=window_size,
            similarity_threshold=similarity_threshold,
        )
        self.workflow = SageFlowServiceWorkflowRunner(adapter=adapter)

    def reset(self) -> None:
        self.workflow.reset()

    def ingest_events(
        self,
        events: list[VectorStreamEvent | dict[str, Any]],
    ) -> SageFlowDemoRunResult:
        resolved_events = [
            item if isinstance(item, dict) else coerce_vector_stream_event(item)
            for item in events
        ]
        insights = self.workflow.ingest_events(resolved_events)
        return SageFlowDemoRunResult(
            processed_event_count=len(resolved_events),
            insight_count=len(insights),
            insights=insights,
            final_snapshot=self.workflow.get_latest_snapshot(),
        )

    def run_demo(self, *, reset: bool = True, dataset: str = "baseline") -> SageFlowDemoRunResult:
        if reset:
            self.reset()
        return self.ingest_events(build_demo_vector_events(dataset))

    def get_latest_snapshot(self) -> SageFlowWindowSnapshot | None:
        return self.workflow.get_latest_snapshot()

    def get_demo_summary(self, dataset: str = "baseline") -> dict[str, int]:
        return build_demo_summary(dataset)

    def to_payload(self, result: SageFlowDemoRunResult) -> dict[str, Any]:
        return _to_payload(result)


class SageFlowTriageRoutingApplication:
    """Routing-contract demo over the same persistent SageFlow runtime boundary."""

    def __init__(
        self,
        *,
        window_size: int = 16,
        similarity_threshold: float = 0.985,
    ) -> None:
        self.adapter = InMemorySageFlowSnapshotAdapter(
            window_size=window_size,
            similarity_threshold=similarity_threshold,
        )

    def reset(self) -> None:
        self.adapter.reset()

    def run_demo(self, *, reset: bool = True, dataset: str = "baseline") -> list[TriageRouteDecision]:
        if reset:
            self.reset()
        events = build_demo_vector_events(dataset)
        decisions: list[TriageRouteDecision] = []
        for event in events:
            self.adapter.process_event(event)
        snapshot = self.adapter.get_latest_snapshot()
        for event in events:
            decisions.append(_route_from_snapshot(event, snapshot))
        return decisions

    def to_payload(self, decisions: list[TriageRouteDecision]) -> list[dict[str, Any]]:
        return _to_payload(decisions)


class SageFlowSecurityEscalationApplication:
    """Escalation-contract demo driven by corroborating join evidence."""

    def __init__(
        self,
        *,
        window_size: int = 32,
        similarity_threshold: float = 0.985,
    ) -> None:
        self.adapter = InMemorySageFlowSnapshotAdapter(
            window_size=window_size,
            similarity_threshold=similarity_threshold,
        )

    def reset(self) -> None:
        self.adapter.reset()

    def run_demo(self, *, reset: bool = True, dataset: str = "baseline") -> list[SecurityEscalationSignal]:
        if reset:
            self.reset()
        signals: list[SecurityEscalationSignal] = []
        for event in build_security_demo_vector_events(dataset):
            response = self.adapter.process_event(event)
            signals.append(_security_signal_from_response(response))
        return signals

    def to_payload(self, signals: list[SecurityEscalationSignal]) -> list[dict[str, Any]]:
        return _to_payload(signals)


def _route_from_response(
    event: VectorStreamEvent,
    neighbors: list[Any],
) -> TriageRouteDecision:
    tags = set(event.tags)
    route = "vulnerability-intake"
    priority = "p2"
    if {"pan-os", "globalprotect"} & tags:
        route = "edge-firewall-response"
        priority = "p0"
    elif {"xz-utils", "liblzma", "supply-chain"} & tags:
        route = "linux-supply-chain-response"
        priority = "p0"
    elif {"openssh", "regresshion", "sshd"} & tags:
        route = "identity-access-response"
        priority = "p1"
    elif {"php", "php-cgi"} & tags:
        route = "web-platform-response"
        priority = "p1"
    elif {"fortios", "fortiproxy", "ssl-vpn"} & tags:
        route = "edge-vpn-response"
        priority = "p0"
    elif {"teamcity", "ci-cd"} & tags:
        route = "ci-cd-platform-response"
        priority = "p0"

    focus_sources = sorted({event.source, *(item.source for item in neighbors)})
    neighbor_ids = [item.event_id for item in neighbors]
    return TriageRouteDecision(
        event_id=event.event_id,
        route=route,
        priority=priority,
        focus_sources=focus_sources,
        supporting_neighbor_ids=neighbor_ids,
        rationale=f"{event.event_id} routed to {route} using {len(neighbor_ids)} SageFlow Top-K neighbors.",
    )


def _route_from_snapshot(
    event: VectorStreamEvent,
    snapshot: SageFlowWindowSnapshot | None,
) -> TriageRouteDecision:
    neighbors: list[Any] = []
    if snapshot is not None:
        for cluster in snapshot.hot_clusters:
            if event.event_id not in cluster.member_ids:
                continue
            source_by_id = {event.event_id: event.source}
            neighbor_ids = [item for item in cluster.member_ids if item != event.event_id]
            neighbors = [
                type("Neighbor", (), {"event_id": item, "source": source_by_id.get(item, "runtime_context")})()
                for item in neighbor_ids
            ]
            break
    return _route_from_response(event, neighbors)


def _security_signal_from_response(response: Any) -> SecurityEscalationSignal:
    event = response.event
    cluster = response.active_cluster
    neighbors = [item.event_id for item in response.nearest_neighbors]
    critical_tags = {
        "exploited",
        "kev",
        "rce",
        "remote-code-execution",
        "command-injection",
        "auth-bypass",
        "signal-race",
        "ssh-backdoor",
    }
    corroborated = cluster.size >= 3 or len(neighbors) >= 2
    critical = event.severity >= 0.94 and (corroborated or bool(critical_tags & set(event.tags)))

    action = "watchlist-with-context"
    severity = "high" if event.severity >= 0.90 else "medium"
    if critical:
        action = "page-vulnerability-oncall"
        severity = "critical"

    return SecurityEscalationSignal(
        event_id=event.event_id,
        action=action,
        severity=severity,
        supporting_neighbor_ids=neighbors,
        related_cluster_id=cluster.cluster_id,
        rationale=(
            f"{event.event_id} has severity {event.severity:.2f}, "
            f"{cluster.size} clustered records, and {len(neighbors)} corroborating neighbors."
        ),
    )
