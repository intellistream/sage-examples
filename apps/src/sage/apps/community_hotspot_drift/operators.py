from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(path_str: str) -> list[dict[str, Any]]:
    path = Path(path_str)
    if not path.exists():
        return [{"source_path": path_str, "text": path.name or path_str}]
    if path.is_dir():
        items: list[dict[str, Any]] = []
        for child in sorted(path.iterdir()):
            if child.is_file():
                items.extend(_load_records(str(child)))
        return items
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {"value": item} for item in data]
        if isinstance(data, dict):
            return [data]
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=delimiter))
    return [{"text": path.read_text(encoding="utf-8-sig"), "source_path": str(path)}]


class CommunityEventSource(ListBatchSource):
    def __init__(self, event_file: str, **kwargs):
        super().__init__(**kwargs)
        self.event_file = event_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.event_file)
        for item in items:
            item.setdefault("app_slug", "community_hotspot_drift")
            item.setdefault("source_path", self.event_file)
        return items


class CommunityZoneMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["zone"] = str(payload.get("zone") or payload.get("district") or "unknown")
        payload["current_count"] = int(
            float(payload.get("current_count") or payload.get("count_current") or 0)
        )
        payload["previous_count"] = int(
            float(payload.get("previous_count") or payload.get("count_previous") or 0)
        )
        payload["issue_type"] = str(payload.get("issue_type") or payload.get("topic") or "general")
        return payload


class CommunityTopicAggregator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        current_count = int(payload.get("current_count") or 0)
        previous_count = int(payload.get("previous_count") or 0)
        delta = current_count - previous_count
        payload["topic_delta"] = delta
        payload["drift_ratio"] = (
            round((current_count / max(previous_count, 1)), 2) if current_count else 0.0
        )
        return payload


class HotspotDriftDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        delta = int(payload.get("topic_delta") or 0)
        ratio = float(payload.get("drift_ratio") or 0.0)
        drift_status = "stable"
        if delta >= 10 or ratio >= 2.0:
            drift_status = "significant_shift"
        elif delta >= 5 or ratio >= 1.3:
            drift_status = "emerging_shift"
        payload["drift_status"] = drift_status
        payload["governance_priority"] = (
            "high"
            if drift_status == "significant_shift"
            else "medium"
            if drift_status == "emerging_shift"
            else "normal"
        )
        payload["insight_summary"] = (
            f"Zone {payload.get('zone')} issue {payload.get('issue_type')} drift {drift_status}, "
            f"priority {payload.get('governance_priority')}."
        )
        return payload


class CommunityInsightSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
