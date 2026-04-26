"""Operators for inventory alerting."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class InventorySource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class InventoryComparator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        current_stock = float(item.get("current_stock") or 0)
        reorder_point = float(item.get("reorder_point") or 0)
        max_stock = float(item.get("max_stock") or reorder_point * 3 or 100)
        item["current_stock"] = current_stock
        item["reorder_point"] = reorder_point
        item["max_stock"] = max_stock
        item["status"] = (
            "low"
            if current_stock < reorder_point
            else "high"
            if current_stock > max_stock
            else "normal"
        )
        return item


class InventoryFeatureBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        enriched = InventoryComparator().execute(item)
        gap = enriched["current_stock"] - enriched["reorder_point"]
        enriched["inventory_gap"] = round(gap, 2)
        return enriched


class AlertGenerator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        status = item.get("status", "normal")
        if status == "low":
            item["alert_message"] = "Reorder required"
        elif status == "high":
            item["alert_message"] = "Excess inventory detected"
        else:
            item["alert_message"] = "Inventory healthy"
        return item


class InventoryAnomalyScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        status = item.get("status", "normal")
        item["anomaly_score"] = 2 if status == "low" else 1 if status == "high" else 0
        return item


class AlertLevelMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item = AlertGenerator().execute(item)
        score = int(item.get("anomaly_score", 0))
        item["alert_level"] = "high" if score >= 2 else "medium" if score == 1 else "low"
        return item


class AlertSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        Path(self.output_file).write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
