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


class BudgetPlanSource(ListBatchSource):
    def __init__(self, plan_file: str, actual_file: str, **kwargs):
        super().__init__(**kwargs)
        self.plan_file = plan_file
        self.actual_file = actual_file

    def load_items(self) -> list[dict[str, Any]]:
        plans = _load_records(self.plan_file)
        actuals = _load_records(self.actual_file)
        actual_index = {
            str(item.get("cost_center") or item.get("category") or ""): item for item in actuals
        }
        for item in plans:
            key = str(item.get("cost_center") or item.get("category") or "")
            item.setdefault("app_slug", "budget_variance_alert")
            item["actual_record"] = actual_index.get(key, {})
            item.setdefault("source_path", self.plan_file)
        return plans


class BudgetCategoryMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        actual = payload.get("actual_record") or {}
        payload["cost_center"] = str(
            payload.get("cost_center") or payload.get("category") or "unknown"
        )
        payload["planned_amount"] = _to_float(
            payload.get("planned_amount") or payload.get("budget")
        )
        payload["actual_amount"] = _to_float(actual.get("actual_amount") or actual.get("spent"))
        payload["progress_pct"] = _to_float(
            actual.get("progress_pct") or payload.get("progress_pct")
        )
        return payload


class BudgetVarianceDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        planned = payload.get("planned_amount", 0.0)
        actual = payload.get("actual_amount", 0.0)
        variance = actual - planned
        ratio = round((actual / planned), 2) if planned else 0.0
        alerts: list[str] = []
        if variance > 0:
            alerts.append("overspend")
        if payload.get("progress_pct", 100.0) < 50 and ratio > 0.7:
            alerts.append("spend_ahead_of_progress")
        payload["variance_amount"] = round(variance, 2)
        payload["variance_ratio"] = ratio
        payload["alert_level"] = "critical" if ratio >= 1.2 else "watch" if alerts else "normal"
        payload["variance_summary"] = (
            f"Cost center {payload.get('cost_center')} variance {payload.get('variance_amount')}, "
            f"alert {payload.get('alert_level')} ({', '.join(alerts) or 'none'})."
        )
        return payload


class BudgetAlertSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("actual_record", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
