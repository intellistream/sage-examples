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


class TrafficEventSource(ListBatchSource):
    def __init__(self, event_file: str, **kwargs):
        super().__init__(**kwargs)
        self.event_file = event_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.event_file)
        for item in items:
            item.setdefault("app_slug", "traffic_briefing")
            item.setdefault("source_path", self.event_file)
        return items


class TrafficEventMerger(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["event_type"] = str(payload.get("event_type") or payload.get("type") or "incident")
        payload["location"] = str(payload.get("location") or payload.get("road") or "unknown")
        payload["lanes_blocked"] = int(_to_float(payload.get("lanes_blocked")))
        payload["weather_impact"] = str(payload.get("weather_impact") or "none")
        return payload


class TrafficImpactScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = 0.0
        if payload.get("event_type") in {"accident", "collision"}:
            score += 4
        score += int(payload.get("lanes_blocked") or 0) * 2
        if payload.get("weather_impact") not in {"none", "clear", ""}:
            score += 2
        payload["impact_score"] = score
        payload["dispatch_priority"] = (
            "high" if score >= 6 else "medium" if score >= 3 else "normal"
        )
        return payload


class TrafficBriefFormatter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["brief_summary"] = (
            f"{payload.get('event_type')} at {payload.get('location')}, lanes blocked {payload.get('lanes_blocked')}, "
            f"priority {payload.get('dispatch_priority')}."
        )
        return payload


class TrafficBriefSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
