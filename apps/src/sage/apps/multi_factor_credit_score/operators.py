from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class UserCreditSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class FactorCollector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["income_score"] = float(item.get("income_score") or 0)
        item["repayment_score"] = float(item.get("repayment_score") or 0)
        item["asset_score"] = float(item.get("asset_score") or 0)
        return item


class CreditAggregator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = (
            item["income_score"] * 0.3 + item["repayment_score"] * 0.5 + item["asset_score"] * 0.2
        )
        item["composite_credit_score"] = round(score, 2)
        item["segment"] = "excellent" if score >= 85 else "good" if score >= 65 else "watch"
        return item


class CreditResultSink(SinkFunction):
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
