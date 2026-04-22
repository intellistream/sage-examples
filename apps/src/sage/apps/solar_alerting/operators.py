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


class SolarSignalSource(ListBatchSource):
    def __init__(self, sensor_file: str, weather_file: str, **kwargs):
        super().__init__(**kwargs)
        self.sensor_file = sensor_file
        self.weather_file = weather_file

    def load_items(self) -> list[dict[str, Any]]:
        signals = _load_records(self.sensor_file)
        weather = _load_records(self.weather_file)
        weather_ref = weather[0] if weather else {}
        for item in signals:
            item.setdefault("app_slug", "solar_alerting")
            item["weather_ref"] = weather_ref
            item.setdefault("source_path", self.sensor_file)
        return signals


class SolarWeatherJoiner(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        weather = payload.get("weather_ref") or {}
        payload["power_kw"] = _to_float(payload.get("power_kw"))
        payload["expected_irradiance"] = _to_float(weather.get("irradiance_wm2"), 800)
        payload["cloud_cover_pct"] = _to_float(weather.get("cloud_cover_pct"))
        return payload


class SolarAnomalyDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues: list[str] = []
        if payload.get("power_kw", 0.0) < 50 and payload.get("expected_irradiance", 0.0) > 700:
            issues.append("under_generation")
        if str(payload.get("device_status") or "").lower() in {"offline", "fault"}:
            issues.append("device_fault")
        if payload.get("cloud_cover_pct", 0.0) > 80:
            issues.append("weather_limited")
        payload["solar_flags"] = issues
        return payload


class SolarPriorityScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = len(payload.get("solar_flags") or []) * 3
        priority = "normal"
        if "device_fault" in (payload.get("solar_flags") or []):
            score += 3
        if score >= 6:
            priority = "high"
        elif score >= 3:
            priority = "watch"
        payload["alert_priority"] = priority
        payload["alert_summary"] = (
            f"Site alert priority {priority}, flags {', '.join(payload.get('solar_flags') or []) or 'none'}."
        )
        return payload


class SolarAlertSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("weather_ref", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
