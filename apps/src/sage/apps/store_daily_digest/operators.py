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


class StoreOpsSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "store_daily_digest")
            item.setdefault("source_path", self.input_dir)
        return items


class StoreMetricAggregator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["sales"] = _to_float(payload.get("sales"))
        payload["stockouts"] = int(_to_float(payload.get("stockouts")))
        payload["complaints"] = int(_to_float(payload.get("complaints")))
        payload["shrinkage"] = _to_float(payload.get("shrinkage"))
        return payload


class StoreExceptionDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues: list[str] = []
        if payload.get("stockouts", 0) > 5:
            issues.append("high_stockouts")
        if payload.get("complaints", 0) > 3:
            issues.append("high_customer_complaints")
        if payload.get("shrinkage", 0.0) > 1000:
            issues.append("high_shrinkage")
        payload["daily_exceptions"] = issues
        return payload


class StoreActionBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        actions: list[str] = []
        if "high_stockouts" in (payload.get("daily_exceptions") or []):
            actions.append("replenish_fast_moving_items")
        if "high_customer_complaints" in (payload.get("daily_exceptions") or []):
            actions.append("review_service_shift_and_queue")
        if "high_shrinkage" in (payload.get("daily_exceptions") or []):
            actions.append("audit_inventory_and_loss_prevention")
        payload["next_day_actions"] = actions or ["maintain_normal_operations"]
        payload["digest_summary"] = (
            f"Sales {payload.get('sales')}, exceptions {', '.join(payload.get('daily_exceptions') or []) or 'none'}, "
            f"actions {', '.join(payload.get('next_day_actions') or [])}."
        )
        return payload


class StoreDigestSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
