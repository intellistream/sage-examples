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


class SensorSource(ListBatchSource):
    def __init__(self, sensor_file: str, **kwargs):
        super().__init__(**kwargs)
        self.sensor_file = sensor_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.sensor_file)
        for item in items:
            item.setdefault("app_slug", "factory_watch")
            item.setdefault("source_path", self.sensor_file)
        return items


class SensorDeviceMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["device_id"] = str(payload.get("device_id") or payload.get("machine") or "unknown")
        payload["station"] = str(payload.get("station") or payload.get("line") or "line-a")
        payload["temperature_c"] = _to_float(payload.get("temperature_c"))
        payload["pressure_kpa"] = _to_float(payload.get("pressure_kpa"))
        payload["vibration_mm_s"] = _to_float(payload.get("vibration_mm_s"))
        return payload


class SensorAnomalyScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues: list[str] = []
        score = 0.0
        if payload.get("temperature_c", 0.0) > 85:
            issues.append("high_temperature")
            score += 4
        if payload.get("pressure_kpa", 0.0) > 220:
            issues.append("high_pressure")
            score += 3
        if payload.get("vibration_mm_s", 0.0) > 12:
            issues.append("high_vibration")
            score += 4
        payload["anomaly_flags"] = issues
        payload["anomaly_score"] = score
        return payload


class SensorAlertLeveler(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        level = "normal"
        if payload.get("anomaly_score", 0.0) >= 7:
            level = "critical"
        elif payload.get("anomaly_score", 0.0) >= 3:
            level = "watch"
        payload["alert_level"] = level
        payload["inspection_hint"] = (
            "check cooling and bearing health"
            if level != "normal"
            else "continue routine monitoring"
        )
        payload["alert_summary"] = (
            f"Device {payload.get('device_id')} at {payload.get('station')} level {level}, "
            f"flags {', '.join(payload.get('anomaly_flags') or []) or 'none'}."
        )
        return payload


class SensorWatchSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
