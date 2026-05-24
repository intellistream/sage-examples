"""Snapshot contracts passed from SageFlow runtime state to upper-layer LLM nodes."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from .models import SageFlowServiceResponse, SnapshotContract

_METADATA_FIELDS = (
    "cve_id",
    "cve",
    "title",
    "description",
    "vendor",
    "product",
    "cvss_score",
    "cvss_severity",
    "cwe",
    "known_exploited",
    "known_ransomware_campaign_use",
    "due_date",
    "required_action",
    "source_url",
    "references",
    "published",
    "last_modified",
)


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


def contract_allowed_evidence_ids(contract: SnapshotContract, *, neighbor_limit: int = 8) -> list[str]:
    ids = [contract.query_event.event_id, *[item.event_id for item in contract.neighbors[:neighbor_limit]]]
    ids.extend(contract.cluster.member_ids)
    return sorted(dict.fromkeys(ids))


def build_snapshot_prompt(contract: SnapshotContract) -> str:
    """Render the contract into a compact, evidence-grounded LLM prompt."""

    event = contract.query_event
    neighbor_rows = [
        {
            "event_id": item.event_id,
            "source": item.source,
            "similarity": round(item.similarity, 4),
            "summary": item.summary,
            "metadata": _compact_metadata(item.metadata),
        }
        for item in contract.neighbors[:8]
    ]
    runtime_payload = contract.runtime.to_dict() if contract.runtime is not None else {}
    source_consensus = _source_consensus(
        [event.source, *[item.source for item in contract.neighbors[:8]]]
    )
    allowed_evidence_ids = contract_allowed_evidence_ids(contract)
    payload = {
        "task": (
            "Generate a concise vulnerability intelligence response grounded only in the "
            "evidence ids supplied by the vector-window runtime."
        ),
        "contract_controls": {
            "contract_id": contract.contract_id,
            "contract_type": contract.contract_type,
            "allowed_evidence_ids": allowed_evidence_ids,
            "citation_policy": "Cite event ids from allowed_evidence_ids for every factual claim.",
            "unknown_policy": "Say that evidence is insufficient instead of inventing facts.",
        },
        "query_event": {
            "event_id": event.event_id,
            "source": event.source,
            "timestamp": event.timestamp,
            "severity": event.severity,
            "tags": list(event.tags),
            "summary": event.summary,
            "metadata": _compact_metadata(event.metadata),
        },
        "neighbors": neighbor_rows,
        "cluster": {
            **contract.cluster.to_dict(),
            "source_consensus": source_consensus,
        },
        "runtime_trace": runtime_payload,
    }
    return (
        "You are an incident-response assistant. Use only the supplied evidence. "
        "Cite event ids when making claims. Return four short sections: incident family, risk, "
        "evidence, and next actions. Do not mention sources outside allowed_evidence_ids.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _compact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in _METADATA_FIELDS:
        if key not in metadata:
            continue
        value = metadata[key]
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            compact[key] = [str(item) for item in value[:5]]
        elif isinstance(value, dict):
            compact[key] = {
                str(child_key): str(child_value)
                for child_key, child_value in list(value.items())[:8]
                if child_value not in (None, "", [], {})
            }
        else:
            compact[key] = value
    return compact


def _source_consensus(sources: list[str]) -> dict[str, Any]:
    counter = Counter(source for source in sources if source)
    return {
        "distinct_source_count": len(counter),
        "source_breakdown": dict(counter),
        "cross_source": len(counter) >= 2,
    }
