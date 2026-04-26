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


class CarbonDataSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "carbon_collection")
            item.setdefault("source_path", self.input_dir)
        return items


class CarbonFieldExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["activity_type"] = str(
            payload.get("activity_type") or payload.get("source_type") or "energy"
        )
        payload["amount"] = _to_float(payload.get("amount") or payload.get("value"))
        payload["unit"] = str(payload.get("unit") or "kwh")
        return payload


class CarbonUnitNormalizer(MapFunction):
    FACTORS = {"kwh": 0.0007, "km": 0.0002, "kg": 0.001}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        factor = self.FACTORS.get(str(payload.get("unit") or "").lower(), 0.001)
        payload["emissions_tco2e"] = round(payload.get("amount", 0.0) * factor, 4)
        return payload


class CarbonLedgerBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["ledger_status"] = "missing_data" if payload.get("amount", 0.0) == 0 else "ready"
        payload["ledger_summary"] = (
            f"Activity {payload.get('activity_type')} emitted {payload.get('emissions_tco2e')} tCO2e, status {payload.get('ledger_status')}."
        )
        return payload


class CarbonCollectionSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
