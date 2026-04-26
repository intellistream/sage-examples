from __future__ import annotations

import csv
import json
from datetime import datetime
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


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


class LabRecordSource(ListBatchSource):
    def __init__(self, record_file: str, **kwargs):
        super().__init__(**kwargs)
        self.record_file = record_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.record_file)
        for item in items:
            item.setdefault("app_slug", "lab_turnaround_alert")
            item.setdefault("source_path", self.record_file)
        return items


class LabStageMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["collected_at"] = _parse_dt(payload.get("collected_at"))
        payload["received_at"] = _parse_dt(payload.get("received_at"))
        payload["reported_at"] = _parse_dt(payload.get("reported_at"))
        payload["test_type"] = str(payload.get("test_type") or "routine")
        return payload


class TurnaroundTimeBuilder(MapFunction):
    TARGET_HOURS = {"routine": 8, "chemistry": 6, "pathology": 24, "urgent": 2}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        collected = payload.get("collected_at")
        received = payload.get("received_at")
        reported = payload.get("reported_at")
        collect_to_receive = (
            ((received - collected).total_seconds() / 3600) if collected and received else None
        )
        receive_to_report = (
            ((reported - received).total_seconds() / 3600) if received and reported else None
        )
        total = ((reported - collected).total_seconds() / 3600) if collected and reported else None
        payload["collect_to_receive_hours"] = (
            round(collect_to_receive, 2) if collect_to_receive is not None else None
        )
        payload["receive_to_report_hours"] = (
            round(receive_to_report, 2) if receive_to_report is not None else None
        )
        payload["total_turnaround_hours"] = round(total, 2) if total is not None else None
        payload["target_hours"] = self.TARGET_HOURS.get(payload.get("test_type"), 8)
        return payload


class TurnaroundAnomalyDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        blockers: list[str] = []
        if (
            payload.get("collect_to_receive_hours") is not None
            and float(payload["collect_to_receive_hours"]) > 2
        ):
            blockers.append("transport_delay")
        if (
            payload.get("receive_to_report_hours") is not None
            and float(payload["receive_to_report_hours"])
            > float(payload.get("target_hours") or 8) * 0.75
        ):
            blockers.append("lab_processing_delay")
        if payload.get("total_turnaround_hours") is not None and float(
            payload["total_turnaround_hours"]
        ) > float(payload.get("target_hours") or 8):
            blockers.append("sla_breach")
        payload["turnaround_alert_level"] = (
            "critical" if "sla_breach" in blockers else "watch" if blockers else "normal"
        )
        payload["bottleneck_stage"] = blockers[0] if blockers else "none"
        payload["alert_summary"] = (
            f"样本 {payload.get('sample_id', 'unknown')} 周转 {payload.get('total_turnaround_hours')} 小时，"
            f"状态 {payload.get('turnaround_alert_level')}。"
        )
        return payload


class LabAlertSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        for field in ("collected_at", "received_at", "reported_at"):
            if payload.get(field) is not None:
                payload[field] = payload[field].isoformat()
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
