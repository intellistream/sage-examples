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


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class RepairTicketSource(ListBatchSource):
    def __init__(self, ticket_file: str, **kwargs):
        super().__init__(**kwargs)
        self.ticket_file = ticket_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.ticket_file)
        for item in items:
            item.setdefault("app_slug", "urban_repair_scheduler")
            item.setdefault("source_path", self.ticket_file)
        return items


class RepairGeoMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["district"] = str(payload.get("district") or payload.get("zone") or "unknown")
        payload["asset_type"] = str(
            payload.get("asset_type") or payload.get("category") or "infrastructure"
        )
        payload["street"] = str(payload.get("street") or payload.get("location") or "unknown")
        return payload


class RepairPriorityScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        severity = _to_float(payload.get("severity"), 1.0)
        public_safety = str(payload.get("public_safety_risk") or "false").lower() in {
            "true",
            "1",
            "yes",
        }
        score = severity * 2 + (3 if public_safety else 0)
        if payload.get("asset_type") in {"road", "manhole", "streetlight"}:
            score += 1
        payload["priority_score"] = score
        payload["dispatch_priority"] = (
            "high" if score >= 6 else "medium" if score >= 3 else "normal"
        )
        return payload


class RepairRoutePlanner(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        district = payload.get("district")
        street = payload.get("street")
        asset = payload.get("asset_type")
        payload["crew_type"] = f"{asset}_crew"
        payload["route_bucket"] = f"{district}:{street}"
        payload["schedule_summary"] = (
            f"Dispatch {payload.get('crew_type')} to {payload.get('route_bucket')} with priority {payload.get('dispatch_priority')}."
        )
        return payload


class RepairScheduleSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
