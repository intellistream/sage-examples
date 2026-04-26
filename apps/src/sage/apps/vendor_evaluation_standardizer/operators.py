from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class VendorEvaluationSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class EvaluationFieldMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["vendor_id"] = (
            item.get("vendor_id") or item.get("supplier_id") or item.get("id") or "unknown"
        )
        item["vendor_name"] = (
            item.get("vendor_name") or item.get("supplier_name") or item.get("name") or "unknown"
        )
        item["raw_score"] = item.get("raw_score") or item.get("score") or item.get("rating") or 0
        item["evaluation_comment"] = (
            item.get("evaluation_comment") or item.get("comment") or item.get("remark") or ""
        )
        return item


class EvaluationNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = float(item.get("raw_score") or 0)
        normalized_score = max(0.0, min(score, 100.0))
        item["normalized_score"] = round(normalized_score, 2)
        item["evaluation_level"] = (
            "excellent"
            if normalized_score >= 85
            else "watch"
            if normalized_score < 60
            else "stable"
        )
        return item


class VendorRiskMarker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        comment = str(item.get("evaluation_comment", "")).lower()
        risk_terms = ("delay", "penalty", "quality", "complaint", "breach")
        risk_hits = sum(1 for term in risk_terms if term in comment)
        if item.get("normalized_score", 0) < 60:
            risk_hits += 1
        item["risk_marker"] = "high" if risk_hits >= 2 else "medium" if risk_hits == 1 else "low"
        return item


class VendorEvaluationSink(SinkFunction):
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
