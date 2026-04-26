from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class VisitorFlowSource(ListBatchSource):
    def __init__(self, flow_file: str, **kwargs):
        super().__init__(**kwargs)
        self.flow_file = flow_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.flow_file, encoding="utf-8", newline="") as handle:
            if self.flow_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class ZoneMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["zone"] = str(item.get("zone") or item.get("hall") or "unknown").strip().lower()
        return item


class HeatScoreCalculator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        visitors = int(float(item.get("visitors") or 0))
        dwell_minutes = float(item.get("dwell_minutes") or 0)
        item["heat_score"] = round(visitors * 0.6 + dwell_minutes * 1.5, 2)
        return item


class CongestionDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = float(item.get("heat_score", 0))
        item["congestion_level"] = "high" if score >= 80 else "medium" if score >= 40 else "low"
        return item


class HeatmapSink(SinkFunction):
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
