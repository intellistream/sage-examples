from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class LeadSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class FeatureScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        company_size = int(float(item.get("company_size") or 0))
        budget = float(item.get("budget") or 0)
        interaction_count = int(float(item.get("interaction_count") or 0))
        score = (
            (2 if company_size >= 500 else 1 if company_size >= 50 else 0)
            + (2 if budget >= 100000 else 1 if budget >= 10000 else 0)
            + min(interaction_count, 3)
        )
        item["lead_score"] = score
        return item


class PriorityRanker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = int(item.get("lead_score", 0))
        item["priority"] = "hot" if score >= 6 else "warm" if score >= 3 else "cold"
        return item


class LeadSink(SinkFunction):
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
