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


class RadiologyReportSource(ListBatchSource):
    def __init__(self, report_file: str, patient_file: str, **kwargs):
        super().__init__(**kwargs)
        self.report_file = report_file
        self.patient_file = patient_file

    def load_items(self) -> list[dict[str, Any]]:
        reports = _load_records(self.report_file)
        patients = _load_records(self.patient_file)
        patient_index = {
            str(patient.get("patient_id") or patient.get("id") or patient.get("mrn") or ""): patient
            for patient in patients
        }
        for item in reports:
            patient_id = str(item.get("patient_id") or item.get("id") or item.get("mrn") or "")
            item["patient_profile"] = patient_index.get(patient_id, {})
            item.setdefault("source_path", self.report_file)
        return reports


class FollowupExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        report_text = str(
            payload.get("report_text") or payload.get("impression") or payload.get("text") or ""
        )
        match = re.search(
            r"follow[- ]?up in\s+(\d+)\s+(day|days|week|weeks|month|months)", report_text, re.I
        )
        days = 0
        if match:
            amount = int(match.group(1))
            unit = match.group(2).lower()
            if "week" in unit:
                days = amount * 7
            elif "month" in unit:
                days = amount * 30
            else:
                days = amount
        payload["followup_required"] = days > 0 or "follow-up" in report_text.lower()
        payload["followup_due_days"] = days or 30
        payload["recommended_modality"] = (
            "CT"
            if "ct" in report_text.lower()
            else "MRI"
            if "mri" in report_text.lower()
            else "ultrasound"
        )
        return payload


class PatientMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        profile = payload.get("patient_profile") or {}
        payload["patient_id"] = str(
            profile.get("patient_id") or payload.get("patient_id") or "unknown"
        )
        payload["patient_name"] = str(
            profile.get("name") or payload.get("patient_name") or "unknown"
        )
        payload["contact_channel"] = str(profile.get("contact_channel") or "phone")
        payload["days_since_report"] = int(float(payload.get("days_since_report") or 0))
        return payload


class FollowupDeadlineChecker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        due_days = int(payload.get("followup_due_days") or 30)
        elapsed = int(payload.get("days_since_report") or 0)
        if not payload.get("followup_required"):
            status = "no_followup_needed"
        elif elapsed > due_days:
            status = "overdue"
        elif elapsed >= max(due_days - 7, 0):
            status = "due_soon"
        else:
            status = "scheduled_window"
        payload["followup_status"] = status
        payload["followup_summary"] = (
            f"患者 {payload.get('patient_name')} 建议 {payload.get('recommended_modality')} 复查，当前状态 {status}。"
        )
        return payload


class FollowupSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("patient_profile", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
