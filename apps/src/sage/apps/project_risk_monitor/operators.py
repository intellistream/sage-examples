from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class ProjectLogSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class RiskKeywordExtractor(MapFunction):
    RISK_TERMS = ("delay", "blocker", "escalation", "overrun", "issue", "risk")

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            str(item.get(field, "")) for field in ("message", "summary", "detail")
        ).lower()
        item["risk_keywords"] = [
            term for term in self.RISK_TERMS if re.search(rf"\b{term}\b", text)
        ]
        return item


class ProjectRiskScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = len(item.get("risk_keywords", []))
        if str(item.get("priority") or "").lower() in {"high", "critical"}:
            score += 1
        item["project_risk_score"] = score
        item["project_risk_level"] = "high" if score >= 3 else "medium" if score >= 1 else "low"
        return item


class ProjectRiskSink(SinkFunction):
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
