from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class SupplyStatusSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class StatusNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        raw_status = str(item.get("status") or item.get("supply_status") or "pending").lower()
        mapping = {
            "in transit": "in_transit",
            "delayed": "delayed",
            "arrived": "arrived",
            "pending": "pending",
        }
        item["normalized_status"] = mapping.get(raw_status, raw_status.replace(" ", "_"))
        item["delay_days"] = int(float(item.get("delay_days") or 0))
        return item


class TimelineBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["timeline"] = [
            {"stage": "order_created", "time": item.get("order_date") or "unknown"},
            {
                "stage": item.get("normalized_status"),
                "time": item.get("status_time") or item.get("update_time") or "unknown",
            },
        ]
        return item


class DelayRiskDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = item.get("delay_days", 0)
        if item.get("normalized_status") == "delayed":
            score += 2
        item["delay_risk_level"] = "high" if score >= 5 else "medium" if score >= 2 else "low"
        return item


class TrackingSink(SinkFunction):
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
