from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class SlotSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class PickingHistorySource(SlotSource):
    pass


class SlotHeatAnalyzer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        picks = int(float(item.get("pick_count") or 0))
        distance = float(item.get("distance_m") or 0)
        item["slot_score"] = round(picks * 0.8 - distance * 0.1, 2)
        return item


class SlotHeatCalculator(SlotHeatAnalyzer):
    pass


class DistanceCostBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["distance_cost"] = round(float(item.get("distance_m") or 0) * 0.1, 2)
        item["slot_score"] = round(float(item.get("slot_score") or 0) - item["distance_cost"], 2)
        return item


class SlotAllocator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = float(item.get("slot_score", 0))
        item["recommended_zone"] = "front" if score >= 50 else "middle" if score >= 20 else "rear"
        return item


class SlotOptimizer(SlotAllocator):
    pass


class SlotSink(SinkFunction):
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


class SlotPlanSink(SlotSink):
    pass
