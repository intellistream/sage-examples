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


class ContractTemplateSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class VersionParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        version_text = str(item.get("version") or item.get("template_version") or "v1.0")
        match = re.search(r"(\d+)(?:\.(\d+))?", version_text)
        major = int(match.group(1)) if match else 1
        minor = int(match.group(2) or 0) if match and match.group(2) else 0
        item["parsed_version"] = {"major": major, "minor": minor}
        return item


class TemplateDiffAnalyzer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        previous_text = str(item.get("previous_template") or "")
        current_text = str(item.get("current_template") or item.get("template") or "")
        previous_tokens = set(re.findall(r"[a-zA-Z_]{4,}", previous_text.lower()))
        current_tokens = set(re.findall(r"[a-zA-Z_]{4,}", current_text.lower()))
        item["added_terms"] = sorted(current_tokens - previous_tokens)
        item["removed_terms"] = sorted(previous_tokens - current_tokens)
        item["change_level"] = (
            "major" if len(item["added_terms"]) + len(item["removed_terms"]) >= 8 else "minor"
        )
        return item


class VersionRegistrySink(SinkFunction):
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
