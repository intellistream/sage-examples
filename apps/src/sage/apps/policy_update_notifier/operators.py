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


class PolicyVersionSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class PolicyDiffExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        previous_text = str(item.get("previous_policy") or item.get("before") or "")
        current_text = str(
            item.get("current_policy") or item.get("after") or item.get("policy") or ""
        )
        before_tokens = set(re.findall(r"[a-zA-Z_]{4,}", previous_text.lower()))
        after_tokens = set(re.findall(r"[a-zA-Z_]{4,}", current_text.lower()))
        item["added_policy_terms"] = sorted(after_tokens - before_tokens)
        item["removed_policy_terms"] = sorted(before_tokens - after_tokens)
        return item


class PolicyImpactAnalyzer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        impact_keywords = {"security", "privacy", "approval", "access", "audit", "compliance"}
        changed = set(item.get("added_policy_terms", [])) | set(
            item.get("removed_policy_terms", [])
        )
        impact_hits = sorted(changed & impact_keywords)
        item["policy_impact_areas"] = impact_hits
        item["policy_notice_level"] = (
            "high" if len(impact_hits) >= 2 else "medium" if impact_hits else "low"
        )
        return item


class PolicyNoticeSink(SinkFunction):
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
