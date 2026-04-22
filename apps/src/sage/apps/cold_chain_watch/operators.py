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


class ColdChainRecordSource(ListBatchSource):
    def __init__(self, record_file: str, **kwargs):
        super().__init__(**kwargs)
        self.record_file = record_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.record_file)
        for item in items:
            item.setdefault("app_slug", "cold_chain_watch")
            item.setdefault("source_path", self.record_file)
        return items


class ColdChainBatchMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["batch_id"] = str(payload.get("batch_id") or payload.get("lot") or "unknown")
        payload["vehicle_id"] = str(payload.get("vehicle_id") or payload.get("truck") or "unknown")
        payload["temperature_c"] = _to_float(payload.get("temperature_c"))
        payload["min_temp_c"] = _to_float(payload.get("min_temp_c"), 2.0)
        payload["max_temp_c"] = _to_float(payload.get("max_temp_c"), 8.0)
        payload["minutes_out_of_range"] = _to_float(payload.get("minutes_out_of_range"))
        return payload


class TemperatureExcursionDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        excursion_flags: list[str] = []
        if payload.get("temperature_c", 0.0) < payload.get("min_temp_c", 2.0):
            excursion_flags.append("below_range")
        if payload.get("temperature_c", 0.0) > payload.get("max_temp_c", 8.0):
            excursion_flags.append("above_range")
        if payload.get("minutes_out_of_range", 0.0) > 30:
            excursion_flags.append("prolonged_excursion")
        payload["excursion_flags"] = excursion_flags
        payload["excursion_detected"] = bool(excursion_flags)
        return payload


class ColdChainRiskScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = len(payload.get("excursion_flags") or []) * 3
        if payload.get("minutes_out_of_range", 0.0) > 60:
            score += 2
        risk_level = "normal"
        if score >= 6:
            risk_level = "critical"
        elif score >= 3:
            risk_level = "watch"
        payload["risk_level"] = risk_level
        payload["risk_score"] = score
        payload["risk_summary"] = (
            f"Batch {payload.get('batch_id')} on vehicle {payload.get('vehicle_id')} risk {risk_level}, "
            f"flags {', '.join(payload.get('excursion_flags') or []) or 'none'}."
        )
        return payload


class ColdChainSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
