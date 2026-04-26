"""Operators for clause-level contract risk detection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


class ContractSource(ListBatchSource):
    def __init__(self, input_path: str, **kwargs):
        super().__init__(**kwargs)
        self.input_path = Path(input_path)

    def load_items(self) -> list[dict[str, Any]]:
        if self.input_path.is_dir():
            files = [path for path in sorted(self.input_path.iterdir()) if path.is_file()]
        else:
            files = [self.input_path]
        return [
            {"contract_id": path.stem, "text": path.read_text(encoding="utf-8")} for path in files
        ]


class TextExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["normalized_text"] = re.sub(r"\s+", " ", item.get("text", "")).strip()
        return item


class ClauseSegmenter(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        segments = re.split(r"(?:\n+|;|。)", item.get("normalized_text", ""))
        return [
            {
                "contract_id": item.get("contract_id"),
                "clause_index": index + 1,
                "clause_text": clause.strip(),
            }
            for index, clause in enumerate(segments)
            if clause.strip()
        ]


class RiskScorer(MapFunction):
    def __init__(self, rules: dict[str, int] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.rules = rules or {
            "unlimited liability": 3,
            "automatic renewal": 2,
            "exclusive jurisdiction": 2,
            "indemnify": 2,
            "无限责任": 3,
            "自动续约": 2,
            "单方解除": 2,
        }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("clause_text", "").lower()
        hits = [keyword for keyword in self.rules if keyword.lower() in text]
        item["risk_terms"] = hits
        item["risk_score"] = sum(self.rules[keyword] for keyword in hits)
        item["risk_level"] = (
            "high" if item["risk_score"] >= 3 else "medium" if item["risk_score"] >= 1 else "low"
        )
        return item


class RiskReportSink(SinkFunction):
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
