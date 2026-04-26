"""Operators for order anomaly detection."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class OrderSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class FeatureCalculator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        amount = float(item.get("amount") or 0)
        quantity = float(item.get("quantity") or 1)
        item["amount"] = amount
        item["quantity"] = quantity
        item["unit_price"] = round(amount / quantity, 2) if quantity else amount
        return item


class RuleScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = 0
        if float(item.get("amount", 0)) > 10000:
            score += 2
        if float(item.get("quantity", 0)) > 50:
            score += 1
        if float(item.get("unit_price", 0)) <= 0:
            score += 2
        item["anomaly_score"] = score
        item["is_anomaly"] = score >= 2
        return item


class AnomalySink(SinkFunction):
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
