"""Operators for permission audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class AuditLogSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class AuditParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["user_id"] = str(item.get("user_id", "unknown")).strip()
        item["permission"] = str(item.get("permission", "")).strip().lower()
        item["action"] = str(item.get("action", "grant")).strip().lower()
        return item


class AuditLogParser(AuditParser):
    pass


class SensitivePermissionDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        permission = item.get("permission", "")
        item["is_sensitive"] = any(
            keyword in permission for keyword in ["admin", "delete", "export", "grant", "root"]
        )
        return item


class SensitiveActionDetector(SensitivePermissionDetector):
    pass


class RiskScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = 1
        if item.get("is_sensitive"):
            score += 2
        if item.get("action") in {"grant", "elevate"}:
            score += 1
        item["risk_score"] = score
        item["risk_level"] = "high" if score >= 4 else "medium" if score >= 2 else "low"
        return item


class AuditRiskScorer(RiskScorer):
    pass


class AuditSink(SinkFunction):
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
