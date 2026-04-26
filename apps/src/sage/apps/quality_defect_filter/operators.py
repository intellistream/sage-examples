"""Operators for quality defect normalization."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


class QualityReportSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class DefectTextExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        defects = str(item.get("defects") or item.get("description") or "")
        item["defect_items"] = [
            part.strip() for part in defects.replace("|", ";").split(";") if part.strip()
        ]
        return item


class DefectSplitter(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "report_id": item.get("report_id") or item.get("id") or "",
                "defect_text": defect,
                "severity": item.get("severity", "medium"),
            }
            for defect in item.get("defect_items", [])
        ]


class DefectStandardizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("defect_text", "").lower()
        if any(keyword in text for keyword in ["scratch", "dent", "鍒掔棔", "鍑归櫡"]):
            item["category"] = "surface"
        elif any(keyword in text for keyword in ["leak", "crack", "娓楁紡", "瑁傜汗"]):
            item["category"] = "structural"
        else:
            item["category"] = "other"
        return item


class DefectSeverityScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        severity = str(item.get("severity", "medium")).lower()
        text = item.get("defect_text", "").lower()
        score = 2 if severity == "high" else 1 if severity == "medium" else 0
        if any(keyword in text for keyword in ["critical", "鐖嗚", "婕忕數", "safety"]):
            score += 2
        elif any(keyword in text for keyword in ["crack", "leak", "瑁傜汗", "娓楁紡"]):
            score += 1
        item["severity_score"] = score
        item["severity_level"] = "high" if score >= 3 else "medium" if score >= 1 else "low"
        return item


class DefectSink(SinkFunction):
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
