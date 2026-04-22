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


class CampusEmissionSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "campus_emission_report")
            item.setdefault("source_path", self.input_dir)
        return items


class EmissionFactorMapper(MapFunction):
    FACTORS = {"electricity_kwh": 0.0007, "diesel_l": 0.0027, "bus_km": 0.00015}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["campus"] = str(payload.get("campus") or "main")
        payload["source_type"] = str(payload.get("source_type") or "electricity_kwh")
        payload["amount"] = _to_float(payload.get("amount"))
        factor = self.FACTORS.get(payload["source_type"], 0.001)
        payload["emissions_tco2e"] = round(payload["amount"] * factor, 4)
        return payload


class CampusEmissionAggregator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["missing_fields"] = [
            field
            for field in ("campus", "source_type", "amount")
            if payload.get(field) in {None, "", 0.0}
        ]
        payload["report_ready"] = not payload.get("missing_fields")
        return payload


class CampusReportFormatter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["report_summary"] = (
            f"Campus {payload.get('campus')} source {payload.get('source_type')} emissions {payload.get('emissions_tco2e')} tCO2e, "
            f"ready {payload.get('report_ready')}."
        )
        return payload


class CampusReportSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
