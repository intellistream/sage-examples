from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class ComplianceDocSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class ComplianceDocClassifier(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            str(item.get(field, "")) for field in ("title", "content", "doc_type")
        ).lower()
        if "audit" in text or "control" in text:
            label = "audit"
        elif "policy" in text or "procedure" in text:
            label = "policy"
        else:
            label = "general"
        item["compliance_category"] = label
        return item


class ReviewDeadlineChecker(MapFunction):
    def __init__(self, reference_date: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.reference_date = _parse_date(reference_date) if reference_date else date.today()

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        deadline = _parse_date(str(item.get("review_deadline") or item.get("deadline") or ""))
        days_left = (deadline - self.reference_date).days if deadline else None
        item["days_to_review"] = days_left
        item["review_status"] = (
            "overdue"
            if days_left is not None and days_left < 0
            else "due_soon"
            if days_left is not None and days_left <= 7
            else "scheduled"
        )
        return item


class ComplianceReminderSink(SinkFunction):
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
