"""Snapshot contracts passed from SageFlow runtime state to upper-layer LLM nodes."""

from __future__ import annotations

import hashlib
import json

from .models import SageFlowServiceResponse, SnapshotContract


def build_snapshot_contract(response: SageFlowServiceResponse) -> SnapshotContract:
    """Build a bounded, serializable evidence contract from a runtime response."""

    evidence_ids = [response.event.event_id, *[item.event_id for item in response.nearest_neighbors]]
    digest = hashlib.sha1("|".join(evidence_ids).encode("utf-8")).hexdigest()[:12]
    contract_type = "snapshot" if response.active_cluster.size >= 3 else "escalation"
    return SnapshotContract(
        contract_id=f"{contract_type}-{response.event.event_id}-{digest}",
        latest_event_id=response.event.event_id,
        query_event=response.event,
        neighbors=list(response.nearest_neighbors),
        cluster=response.active_cluster,
        runtime=response.runtime_info,
        contract_type=contract_type,
    )


def contract_evidence_ids(contract: SnapshotContract, *, limit: int = 4) -> list[str]:
    return [contract.query_event.event_id, *[item.event_id for item in contract.neighbors[: max(limit - 1, 0)]]]


def build_snapshot_prompt(contract: SnapshotContract) -> str:
    """Render the contract into a compact, evidence-grounded LLM prompt."""

    event = contract.query_event
    neighbor_rows = [
        {
            "event_id": item.event_id,
            "source": item.source,
            "similarity": round(item.similarity, 4),
            "summary": item.summary,
        }
        for item in contract.neighbors[:5]
    ]
    runtime_payload = contract.runtime.to_dict() if contract.runtime is not None else {}
    payload = {
        "task": "Generate a concise vulnerability intelligence response grounded only in the evidence ids below.",
        "query_event": {
            "event_id": event.event_id,
            "source": event.source,
            "timestamp": event.timestamp,
            "severity": event.severity,
            "tags": list(event.tags),
            "summary": event.summary,
        },
        "neighbors": neighbor_rows,
        "cluster": contract.cluster.to_dict(),
        "runtime": runtime_payload,
    }
    return (
        "You are an incident-response assistant. Use only the supplied evidence. "
        "Cite event ids when making claims. Return: incident family, risk, evidence, and next actions.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
