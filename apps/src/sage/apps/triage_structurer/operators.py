from __future__ import annotations

import csv
import json
import re
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


def _parse_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class TriageRecordSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_file)
        for item in items:
            item.setdefault("app_slug", "triage_structurer")
            item.setdefault("source_path", self.input_file)
        return items


class TriageFieldExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        note = str(
            payload.get("note") or payload.get("chief_complaint") or payload.get("text") or ""
        )
        payload["chief_complaint"] = str(payload.get("chief_complaint") or note)
        payload["temperature_c"] = _parse_float(payload.get("temperature_c"))
        payload["heart_rate"] = _parse_float(payload.get("heart_rate"))
        payload["oxygen_saturation"] = _parse_float(payload.get("oxygen_saturation"))
        payload["systolic_bp"] = _parse_float(payload.get("systolic_bp"))
        if payload["temperature_c"] is None:
            match = re.search(r"temp(?:erature)?[^\d-]*(-?\d+(?:\.\d+)?)", note, re.I)
            payload["temperature_c"] = _parse_float(match.group(1)) if match else None
        return payload


class TriagePriorityAssigner(MapFunction):
    CRITICAL_TERMS = {"chest pain", "stroke", "unconscious", "bleeding", "seizure"}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        note = str(payload.get("chief_complaint") or "").lower()
        priority = "standard"
        reasons: list[str] = []
        if (
            payload.get("oxygen_saturation") is not None
            and float(payload["oxygen_saturation"]) < 90
        ):
            priority = "emergent"
            reasons.append("low_oxygen")
        if payload.get("systolic_bp") is not None and float(payload["systolic_bp"]) < 90:
            priority = "emergent"
            reasons.append("low_blood_pressure")
        if any(term in note for term in self.CRITICAL_TERMS):
            priority = "emergent"
            reasons.append("critical_complaint")
        elif priority != "emergent":
            if (payload.get("temperature_c") or 0) >= 39 or (payload.get("heart_rate") or 0) >= 120:
                priority = "urgent"
                reasons.append("unstable_vitals")
        payload["triage_priority"] = priority
        payload["triage_reasons"] = reasons or ["routine_intake"]
        return payload


class TriageSummaryBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        complaint = str(payload.get("chief_complaint") or "")
        department = "general_medicine"
        if "chest" in complaint.lower():
            department = "emergency_cardiology"
        elif "breath" in complaint.lower() or "cough" in complaint.lower():
            department = "respiratory"
        payload["recommended_department"] = department
        payload["triage_summary"] = (
            f"主诉: {complaint}; 优先级: {payload.get('triage_priority')}; 建议科室: {department}."
        )
        return payload


class TriageSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
