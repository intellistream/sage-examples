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


class ReturnRecordSource(ListBatchSource):
    def __init__(self, return_file: str, **kwargs):
        super().__init__(**kwargs)
        self.return_file = return_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.return_file)
        for item in items:
            item.setdefault("app_slug", "return_reason_mining")
            item.setdefault("source_path", self.return_file)
        return items


class ReturnFeatureFusion(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["return_text"] = str(
            payload.get("reason_text") or payload.get("customer_note") or ""
        )
        payload["product_category"] = str(payload.get("product_category") or "general")
        payload["service_notes"] = str(payload.get("service_notes") or "")
        return payload


class ReturnReasonClusterer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        text = f"{payload.get('return_text', '')} {payload.get('service_notes', '')}".lower()
        cluster = "other"
        if "size" in text or "fit" in text:
            cluster = "size_issue"
        elif "broken" in text or "damaged" in text:
            cluster = "quality_issue"
        elif "late" in text or "delay" in text:
            cluster = "delivery_issue"
        payload["reason_cluster"] = cluster
        return payload


class ReturnImprovementBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        suggestion = "review ops workflow"
        if payload.get("reason_cluster") == "size_issue":
            suggestion = "improve size chart and fit guidance"
        elif payload.get("reason_cluster") == "quality_issue":
            suggestion = "inspect supplier quality and packaging"
        elif payload.get("reason_cluster") == "delivery_issue":
            suggestion = "review carrier SLA and warehouse dispatch"
        payload["improvement_suggestion"] = suggestion
        payload["mining_summary"] = (
            f"Category {payload.get('product_category')} cluster {payload.get('reason_cluster')}, suggestion {suggestion}."
        )
        return payload


class ReturnMiningSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
