from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class LocationSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class DistanceScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        distance = float(item.get("distance_km") or 0)
        rating = float(item.get("rating") or 0)
        item["recommendation_score"] = round(max(0.0, 10 - distance) + rating * 2, 2)
        return item


class RecommendationFormatter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = float(item.get("recommendation_score", 0))
        item["tier"] = "primary" if score >= 12 else "secondary" if score >= 8 else "candidate"
        return item


class RecommendationSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        ordered = sorted(
            self.items, key=lambda value: value.get("recommendation_score", 0), reverse=True
        )
        Path(self.output_file).write_text(
            json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8"
        )
