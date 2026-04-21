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


class GreenhouseSensorSource(ListBatchSource):
    def __init__(self, sensor_file: str, task_file: str, **kwargs):
        super().__init__(**kwargs)
        self.sensor_file = sensor_file
        self.task_file = task_file

    def load_items(self) -> list[dict[str, Any]]:
        sensors = _load_records(self.sensor_file)
        tasks = _load_records(self.task_file)
        task_index = {str(item.get("zone") or item.get("bed") or ""): item for item in tasks}
        for item in sensors:
            zone = str(item.get("zone") or item.get("bed") or "")
            item.setdefault("app_slug", "greenhouse_assistant")
            item["zone_task"] = task_index.get(zone, {})
            item.setdefault("source_path", self.sensor_file)
        return sensors


class GreenhouseZoneMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["zone"] = str(payload.get("zone") or payload.get("bed") or "unknown")
        payload["temperature_c"] = _to_float(payload.get("temperature_c"))
        payload["humidity_pct"] = _to_float(payload.get("humidity_pct"))
        payload["soil_moisture_pct"] = _to_float(payload.get("soil_moisture_pct"))
        payload["crop"] = str(payload.get("crop") or payload.get("variety") or "general")
        return payload


class ClimateAnomalyDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues: list[str] = []
        if payload.get("temperature_c", 0.0) > 32:
            issues.append("high_temperature")
        if payload.get("humidity_pct", 0.0) > 85:
            issues.append("high_humidity")
        if payload.get("soil_moisture_pct", 100.0) < 25:
            issues.append("low_soil_moisture")
        payload["climate_flags"] = issues
        payload["coordination_level"] = (
            "urgent" if len(issues) >= 2 else "routine" if issues else "stable"
        )
        return payload


class GreenhouseAdviceBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        zone_task = payload.get("zone_task") or {}
        actions: list[str] = []
        if "low_soil_moisture" in (payload.get("climate_flags") or []):
            actions.append("start_irrigation_cycle")
        if "high_humidity" in (payload.get("climate_flags") or []):
            actions.append("increase_ventilation")
        if zone_task.get("inspection_required"):
            actions.append("send_manual_inspection")
        payload["recommended_actions"] = actions or ["continue_monitoring"]
        payload["advice_summary"] = (
            f"Zone {payload.get('zone')} crop {payload.get('crop')} level {payload.get('coordination_level')}, "
            f"actions {', '.join(payload.get('recommended_actions') or [])}."
        )
        return payload


class GreenhouseSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("zone_task", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
