"""SageFlow-as-a-service example application for SAGE."""

from .demo_data import (
    available_demo_datasets,
    build_demo_raw_events,
    build_demo_summary,
    build_demo_vector_events,
    build_replay_order,
    build_security_demo_raw_events,
    build_security_demo_vector_events,
    build_snapshot_demo_sources,
    describe_demo_dataset,
)
from .models import (
    ClusterSnapshot,
    NearestNeighbor,
    SageFlowDemoRunResult,
    SageFlowRuntimeInfo,
    SageFlowServiceResponse,
    SageFlowWindowSnapshot,
    SecurityEscalationSignal,
    TriageRouteDecision,
    VectorSnapshotInsight,
    VectorStreamEvent,
    coerce_vector_stream_event,
)
from .service import (
    SageFlowSecurityEscalationApplication,
    SageFlowServiceDemoApplication,
    SageFlowTriageRoutingApplication,
)

__all__ = [
    "ClusterSnapshot",
    "NearestNeighbor",
    "SageFlowDemoRunResult",
    "SageFlowRuntimeInfo",
    "SageFlowSecurityEscalationApplication",
    "SageFlowServiceDemoApplication",
    "SageFlowServiceResponse",
    "SageFlowTriageRoutingApplication",
    "SageFlowWindowSnapshot",
    "SecurityEscalationSignal",
    "TriageRouteDecision",
    "VectorSnapshotInsight",
    "VectorStreamEvent",
    "available_demo_datasets",
    "build_demo_raw_events",
    "build_demo_summary",
    "build_demo_vector_events",
    "build_replay_order",
    "build_security_demo_raw_events",
    "build_security_demo_vector_events",
    "build_snapshot_demo_sources",
    "coerce_vector_stream_event",
    "describe_demo_dataset",
]
