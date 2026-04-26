"""Operators for user behavior analytics."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class EventSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class EventNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["user_id"] = str(item.get("user_id", "unknown")).strip()
        item["event_type"] = str(item.get("event_type", "unknown")).strip().lower()
        item["value"] = float(item.get("value") or 1)
        return item


class UserAggregator(MapFunction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state: dict[str, dict[str, Any]] = {}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        user_id = item.get("user_id", "unknown")
        profile = self.state.setdefault(
            user_id,
            {"user_id": user_id, "event_count": 0, "total_value": 0.0, "event_types": set()},
        )
        profile["event_count"] += 1
        profile["total_value"] += float(item.get("value", 0))
        profile["event_types"].add(item.get("event_type", "unknown"))
        return {
            "user_id": user_id,
            "event_count": profile["event_count"],
            "total_value": round(profile["total_value"], 2),
            "event_types": sorted(profile["event_types"]),
        }


class AnalyticsSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.latest_by_user: dict[str, dict[str, Any]] = {}

    def execute(self, item: dict[str, Any]) -> None:
        self.latest_by_user[item["user_id"]] = item

    def teardown(self, context: Any) -> None:
        payload = sorted(self.latest_by_user.values(), key=lambda value: value["user_id"])
        Path(self.output_file).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
