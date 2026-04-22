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


class CashflowSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "cashflow_watch")
            item.setdefault("source_path", self.input_dir)
        return items


class CashflowFeatureBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["cash_in"] = _to_float(payload.get("cash_in") or payload.get("receivable"))
        payload["cash_out"] = _to_float(payload.get("cash_out") or payload.get("payable"))
        payload["opening_balance"] = _to_float(payload.get("opening_balance"), 0.0)
        return payload


class CashflowForecaster(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        projected = (
            payload.get("opening_balance", 0.0)
            + payload.get("cash_in", 0.0)
            - payload.get("cash_out", 0.0)
        )
        payload["projected_balance"] = round(projected, 2)
        payload["net_flow"] = round(payload.get("cash_in", 0.0) - payload.get("cash_out", 0.0), 2)
        return payload


class CashflowRiskMarker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        level = "normal"
        if payload.get("projected_balance", 0.0) < 0:
            level = "critical"
        elif payload.get("projected_balance", 0.0) < 10000:
            level = "watch"
        payload["risk_level"] = level
        payload["risk_summary"] = (
            f"Projected balance {payload.get('projected_balance')}, net flow {payload.get('net_flow')}, risk {level}."
        )
        return payload


class CashflowSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
