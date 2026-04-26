from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class EnergySource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class MeterSource(EnergySource):
    pass


class UsageAnalyzer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        consumption = float(item.get("kwh") or 0)
        baseline = float(item.get("baseline_kwh") or 1)
        item["usage_ratio"] = round(consumption / baseline, 2) if baseline else consumption
        return item


class DormMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["dorm_id"] = str(item.get("dorm_id") or item.get("room_no") or "unknown")
        return UsageAnalyzer().execute(item)


class EnergyBaselineComparer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["baseline_delta"] = round(float(item.get("usage_ratio", 0)) - 1.0, 2)
        return item


class RecommendationBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        ratio = float(item.get("usage_ratio", 0))
        item["recommendation"] = (
            "Reduce peak-hour usage" if ratio > 1.2 else "Maintain current plan"
        )
        return item


class EnergyAnomalyDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        compared = EnergyBaselineComparer().execute(item)
        compared["anomaly_level"] = (
            "high"
            if float(compared.get("usage_ratio", 0)) >= 1.5
            else "medium"
            if float(compared.get("usage_ratio", 0)) >= 1.2
            else "low"
        )
        return RecommendationBuilder().execute(compared)


class EnergySink(SinkFunction):
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


class EnergyAdviceSink(EnergySink):
    pass
