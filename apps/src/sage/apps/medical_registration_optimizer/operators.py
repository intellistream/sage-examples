from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class RegistrationSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class RegistrationRequestSource(RegistrationSource):
    pass


class DemandScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        severity = int(float(item.get("severity") or 1))
        wait_days = int(float(item.get("wait_days") or 0))
        item["priority_score"] = severity * 2 + wait_days
        return item


class DoctorSlotFetcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["doctor_slots"] = int(
            float(item.get("doctor_slots") or item.get("available_slots") or 0)
        )
        item["distance_km"] = float(item.get("distance_km") or 0)
        return item


class PatientDoctorMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        scored = DemandScorer().execute(item)
        scored["match_score"] = round(
            scored["priority_score"]
            + max(0.0, 5 - float(scored.get("distance_km", 0)))
            + min(int(scored.get("doctor_slots", 0)), 5),
            2,
        )
        return scored


class SlotAllocator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = int(item.get("priority_score", 0))
        item["recommended_slot"] = (
            "priority_clinic" if score >= 8 else "specialist" if score >= 4 else "general"
        )
        return item


class RegistrationPlanBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        matched = dict(item)
        score = float(matched.get("match_score", matched.get("priority_score", 0)))
        matched["recommended_slot"] = (
            "priority_clinic" if score >= 10 else "specialist" if score >= 6 else "general"
        )
        return matched


class RegistrationSink(SinkFunction):
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
