from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class ShipmentSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class CostCalculator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        weight = float(item.get("weight_kg") or 0)
        distance = float(item.get("distance_km") or 0)
        item["estimated_cost"] = round(weight * 0.8 + distance * 0.2, 2)
        return item


class OptionSelector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        cost = float(item.get("estimated_cost", 0))
        item["recommended_mode"] = (
            "express" if cost <= 50 else "standard" if cost <= 150 else "bulk"
        )
        return item


class LogisticsSink(SinkFunction):
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
