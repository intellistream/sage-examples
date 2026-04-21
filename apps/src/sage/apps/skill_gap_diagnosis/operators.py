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


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


class LearningRecordSource(ListBatchSource):
    def __init__(self, record_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.record_dir = record_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.record_dir)
        for item in items:
            item.setdefault("source_path", self.record_dir)
        return items


class SkillMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["current_skills"] = _as_list(payload.get("current_skills") or payload.get("skills"))
        payload["target_skills"] = _as_list(
            payload.get("target_skills") or payload.get("goal_skills")
        )
        payload["student_id"] = str(
            payload.get("student_id") or payload.get("learner_id") or "unknown"
        )
        return payload


class SkillGapDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        current = set(payload.get("current_skills") or [])
        target = set(payload.get("target_skills") or [])
        missing = sorted(target - current)
        payload["missing_skills"] = missing
        payload["gap_level"] = "high" if len(missing) >= 3 else "medium" if missing else "low"
        return payload


class PracticePathBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        missing = payload.get("missing_skills") or []
        payload["practice_plan"] = [f"补练 {skill} 模块" for skill in missing[:3]] or [
            "维持当前学习节奏"
        ]
        payload["group_recommendation"] = (
            "advanced"
            if payload.get("gap_level") == "low"
            else "support_group"
            if payload.get("gap_level") == "high"
            else "standard"
        )
        return payload


class SkillGapSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
