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


class DataCenterMetricSource(ListBatchSource):
    def __init__(self, metric_file: str, alert_file: str, **kwargs):
        super().__init__(**kwargs)
        self.metric_file = metric_file
        self.alert_file = alert_file

    def load_items(self) -> list[dict[str, Any]]:
        metrics = _load_records(self.metric_file)
        alerts = _load_records(self.alert_file)
        alert_index = {str(item.get("rack_id") or item.get("rack") or ""): item for item in alerts}
        for item in metrics:
            rack_id = str(item.get("rack_id") or item.get("rack") or "")
            item.setdefault("app_slug", "data_center_watch")
            item["alert_ref"] = alert_index.get(rack_id, {})
            item.setdefault("source_path", self.metric_file)
        return metrics


class RackMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["rack_id"] = str(payload.get("rack_id") or payload.get("rack") or "unknown")
        payload["capacity_pct"] = _to_float(payload.get("capacity_pct"))
        payload["temperature_c"] = _to_float(payload.get("temperature_c"))
        payload["power_kw"] = _to_float(payload.get("power_kw"))
        return payload


class CapacityCoolingScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues: list[str] = []
        if payload.get("capacity_pct", 0.0) > 85:
            issues.append("high_capacity")
        if payload.get("temperature_c", 0.0) > 30:
            issues.append("cooling_risk")
        if str((payload.get("alert_ref") or {}).get("alert_type") or "").lower() in {
            "fan_failure",
            "power_alarm",
        }:
            issues.append("active_hardware_alert")
        payload["dc_flags"] = issues
        return payload


class DataCenterRiskMarker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = len(payload.get("dc_flags") or []) * 3
        level = "normal"
        if score >= 6:
            level = "critical"
        elif score >= 3:
            level = "watch"
        payload["risk_level"] = level
        payload["watch_summary"] = (
            f"Rack {payload.get('rack_id')} risk {level}, flags {', '.join(payload.get('dc_flags') or []) or 'none'}."
        )
        return payload


class DataCenterWatchSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("alert_ref", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
