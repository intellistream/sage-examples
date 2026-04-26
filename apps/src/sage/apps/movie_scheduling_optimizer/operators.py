from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class ScreeningSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class HeatScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        popularity = float(item.get("popularity") or 0)
        presale = float(item.get("presale") or 0)
        item["heat_score"] = round(popularity * 0.7 + presale * 0.3, 2)
        return item


class SlotOptimizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = float(item.get("heat_score", 0))
        item["recommended_slot"] = (
            "prime_time" if score >= 80 else "evening" if score >= 50 else "off_peak"
        )
        return item


class ScheduleSink(SinkFunction):
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
