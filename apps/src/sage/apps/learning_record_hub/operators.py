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


class LearningRecordSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class EmployeeMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["employee_id"] = (
            item.get("employee_id") or item.get("staff_id") or item.get("id") or "unknown"
        )
        item["employee_name"] = item.get("employee_name") or item.get("name") or "unknown"
        return item


class CourseNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        course_name = str(
            item.get("course_name") or item.get("course") or "general training"
        ).strip()
        item["course_name"] = course_name.title()
        item["completed_hours"] = float(item.get("completed_hours") or item.get("hours") or 0)
        item["required_hours"] = float(item.get("required_hours") or item.get("target_hours") or 8)
        return item


class CertificationGapDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        gap = max(item.get("required_hours", 0) - item.get("completed_hours", 0), 0)
        item["certification_gap_hours"] = gap
        item["learning_status"] = "complete" if gap == 0 else "pending"
        return item


class LearningProfileSink(SinkFunction):
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
