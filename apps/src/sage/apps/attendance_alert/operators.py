from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class AttendanceSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class AttendanceNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["late_minutes"] = int(float(item.get("late_minutes") or 0))
        item["absent_days"] = int(float(item.get("absent_days") or 0))
        return item


class ScheduleMatcher(MapFunction):
    def __init__(self, schedule_file: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.schedule_file = schedule_file

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["scheduled_shift"] = str(
            item.get("scheduled_shift") or item.get("shift") or "general"
        ).lower()
        item["actual_shift"] = str(
            item.get("actual_shift") or item.get("clock_shift") or item["scheduled_shift"]
        ).lower()
        return AttendanceNormalizer().execute(item)


class AttendanceScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = item["late_minutes"] // 10 + item["absent_days"] * 2
        item["risk_score"] = score
        item["alert_level"] = "high" if score >= 4 else "medium" if score >= 2 else "low"
        return item


class AttendanceAnomalyDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        scored = AttendanceScorer().execute(item)
        if scored.get("scheduled_shift") != scored.get("actual_shift"):
            scored["risk_score"] += 1
            scored["alert_level"] = "high" if scored["risk_score"] >= 4 else "medium"
        return scored


class AttendanceSink(SinkFunction):
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


class AttendanceAlertSink(AttendanceSink):
    pass
