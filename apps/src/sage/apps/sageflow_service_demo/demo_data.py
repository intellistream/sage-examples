"""Repository-local vulnerability intelligence datasets for the ICPP demo."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .models import VectorStreamEvent

DATASET_FILE = Path(__file__).with_name("demo_datasets.json")
EMBEDDING_DIMENSION = 16


def _load_profiles() -> dict[str, dict[str, Any]]:
    with DATASET_FILE.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{DATASET_FILE} must contain at least one dataset profile")
    return payload


def available_demo_datasets() -> list[str]:
    return sorted(_load_profiles())


def _profile(dataset: str) -> dict[str, Any]:
    profiles = _load_profiles()
    try:
        return profiles[dataset]
    except KeyError as exc:
        raise ValueError(f"Unknown demo dataset {dataset!r}; choose one of {sorted(profiles)}") from exc


def _events_by_id(dataset: str, *, include_security_extra: bool = False) -> dict[str, dict[str, Any]]:
    profile = _profile(dataset)
    events = list(profile.get("events", []))
    if include_security_extra:
        events.extend(profile.get("security_extra_events", []))
    event_by_id = {str(item["event_id"]): dict(item) for item in events}
    if len(event_by_id) != len(events):
        raise ValueError(f"Dataset {dataset} contains duplicate event_id values")
    return event_by_id


def build_replay_order(dataset: str = "baseline") -> list[str]:
    return [str(item) for item in _profile(dataset).get("replay_order", [])]


def build_demo_raw_events(dataset: str = "baseline") -> list[dict[str, Any]]:
    event_by_id = _events_by_id(dataset)
    ordered_ids = build_replay_order(dataset) or list(event_by_id)
    return [dict(event_by_id[event_id]) for event_id in ordered_ids]


def build_security_demo_raw_events(dataset: str = "baseline") -> list[dict[str, Any]]:
    event_by_id = _events_by_id(dataset, include_security_extra=True)
    ordered_ids = [*build_replay_order(dataset)]
    ordered_ids.extend(
        str(item["event_id"])
        for item in _profile(dataset).get("security_extra_events", [])
    )
    return [dict(event_by_id[event_id]) for event_id in ordered_ids]


def build_snapshot_demo_sources(
    dataset: str = "baseline",
) -> tuple[list[VectorStreamEvent], list[VectorStreamEvent]]:
    primary_ids = {str(item) for item in _profile(dataset).get("snapshot_primary_ids", [])}
    events = [_to_vector_event(item) for item in build_demo_raw_events(dataset)]
    primary = [event for event in events if event.event_id in primary_ids]
    context = [event for event in events if event.event_id not in primary_ids]
    return primary, context


def build_demo_vector_events(dataset: str = "baseline") -> list[VectorStreamEvent]:
    return [_to_vector_event(item) for item in build_demo_raw_events(dataset)]


def build_security_demo_vector_events(dataset: str = "baseline") -> list[VectorStreamEvent]:
    return [_to_vector_event(item) for item in build_security_demo_raw_events(dataset)]


def build_demo_summary(dataset: str = "baseline") -> dict[str, int]:
    events = build_demo_vector_events(dataset)
    unique_sources = {event.source for event in events}
    return {
        "event_count": len(events),
        "source_count": len(unique_sources),
        "high_severity_events": sum(1 for event in events if event.severity >= 0.90),
    }


def describe_demo_dataset(dataset: str = "baseline") -> dict[str, Any]:
    demo_events = build_demo_raw_events(dataset)
    security_events = build_security_demo_raw_events(dataset)
    primary, _ = build_snapshot_demo_sources(dataset)
    return {
        "dataset": dataset,
        "dataset_file": str(DATASET_FILE),
        "event_count": len(demo_events),
        "security_event_count": len(security_events),
        "source_count": len({item["source"] for item in demo_events}),
        "snapshot_primary_count": len(primary),
        "recommended_window_size": max(len(security_events), 16),
    }


def _to_vector_event(payload: dict[str, Any]) -> VectorStreamEvent:
    if "embedding" in payload:
        return VectorStreamEvent.from_dict(payload)

    enriched = dict(payload)
    enriched["embedding"] = _embed_event(payload)
    return VectorStreamEvent.from_dict(enriched)


def _embed_event(payload: dict[str, Any]) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSION
    tags = [str(item).lower() for item in payload.get("tags", [])]
    summary = str(payload.get("summary", "")).lower()
    text = " ".join([summary, *tags])

    topic_axis = _topic_axis(text)
    vector[topic_axis] = 1.0

    source = str(payload.get("source", "unknown"))
    source_axis = 8 + (_stable_hash(source) % 4)
    vector[source_axis] = 0.025
    vector[12] = float(payload.get("severity", 0.0)) * 0.02
    vector[13] = (_stable_hash(str(payload.get("event_id", ""))) % 17) * 0.0005
    vector[14] = len(tags) * 0.001
    vector[15] = 0.01

    norm = math.sqrt(sum(item * item for item in vector))
    return [round(item / norm, 6) for item in vector]


def _topic_axis(text: str) -> int:
    topic_terms = [
        ("cve-2024-3400", "pan-os", "globalprotect"),
        ("cve-2024-3094", "xz-utils", "liblzma"),
        ("cve-2024-6387", "openssh", "regresshion"),
        ("cve-2024-4577", "php-cgi", "php"),
        ("cve-2024-21762", "fortios", "fortiproxy"),
        ("cve-2024-27198", "teamcity", "ci-cd"),
    ]
    for axis, terms in enumerate(topic_terms):
        if any(term in text for term in terms):
            return axis
    return 7


def _stable_hash(value: str) -> int:
    result = 2166136261
    for char in value.encode("utf-8"):
        result ^= char
        result *= 16777619
        result &= 0xFFFFFFFF
    return result
