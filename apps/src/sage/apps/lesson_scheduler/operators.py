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
    lines = [
        line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
    ]
    return [
        {"text": line, "line_number": index + 1, "source_path": str(path)}
        for index, line in enumerate(lines)
    ]


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


class TeachingRequirementSource(ListBatchSource):
    def __init__(self, plan_file: str, resource_file: str, **kwargs):
        super().__init__(**kwargs)
        self.plan_file = plan_file
        self.resource_file = resource_file

    def load_items(self) -> list[dict[str, Any]]:
        plans = _load_records(self.plan_file)
        resources = _load_records(self.resource_file)
        for item in plans:
            item["resources"] = resources
        return plans


class TeachingConstraintParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["required_hours"] = _parse_int(
            payload.get("required_hours") or payload.get("hours"), 1
        )
        payload["class_size"] = _parse_int(payload.get("class_size") or payload.get("students"), 0)
        preferred_days = str(payload.get("preferred_days") or payload.get("preferred_day") or "")
        payload["preferred_days"] = [
            part.strip() for part in preferred_days.split(",") if part.strip()
        ]
        return payload


class LessonPlanScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        best_room = None
        best_score = -1
        for resource in payload.get("resources") or []:
            capacity = _parse_int(resource.get("capacity"), 0)
            available_hours = _parse_int(resource.get("available_hours"), 0)
            slot_day = str(resource.get("day") or "")
            score = 0
            if capacity >= payload.get("class_size", 0):
                score += 4
            if available_hours >= payload.get("required_hours", 0):
                score += 3
            if slot_day in payload.get("preferred_days", []):
                score += 2
            if score > best_score:
                best_score = score
                best_room = {
                    "room": resource.get("room") or resource.get("resource") or "unassigned",
                    "day": slot_day,
                    "capacity": capacity,
                    "available_hours": available_hours,
                }
        payload["recommended_slot"] = best_room or {
            "room": "unassigned",
            "day": "",
            "capacity": 0,
            "available_hours": 0,
        }
        payload["schedule_score"] = best_score if best_score >= 0 else 0
        return payload


class LessonConflictChecker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        slot = payload.get("recommended_slot") or {}
        conflicts: list[str] = []
        if slot.get("available_hours", 0) < payload.get("required_hours", 0):
            conflicts.append("insufficient_hours")
        if slot.get("capacity", 0) < payload.get("class_size", 0):
            conflicts.append("capacity_shortage")
        payload["conflicts"] = conflicts
        payload["schedule_status"] = "blocked" if conflicts else "scheduled"
        return payload


class LessonScheduleSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("resources", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
