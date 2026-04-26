from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class TranscriptSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class AgendaSegmenter(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        transcript = str(item.get("transcript") or item.get("content") or "")
        segments = [
            segment.strip()
            for segment in re.split(r"\n\s*\n|(?:^|\n)- ", transcript)
            if segment.strip()
        ]
        return [
            {
                **item,
                "segment_index": index,
                "segment_text": segment,
            }
            for index, segment in enumerate(segments, start=1)
        ]


class ActionItemExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        lines = re.split(r"[.;\n]", item.get("segment_text", ""))
        actions = []
        for line in lines:
            text = line.strip()
            lowered = text.lower()
            if any(term in lowered for term in ("will", "action", "todo", "follow up", "owner")):
                actions.append(text)
        item["action_items"] = actions
        return item


class MinutesFormatter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["minutes_entry"] = {
            "segment": item.get("segment_index"),
            "summary": item.get("segment_text", "")[:160],
            "actions": item.get("action_items", []),
        }
        return item


class MinutesSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item.get("minutes_entry", item))

    def teardown(self, context: Any) -> None:
        Path(self.output_file).write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
