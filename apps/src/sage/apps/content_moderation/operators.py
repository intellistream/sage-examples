"""Operators for text moderation."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


class ContentSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            if self.input_file.lower().endswith(".csv"):
                return list(csv.DictReader(handle))
            return [
                {"content_id": str(index + 1), "text": line.strip()}
                for index, line in enumerate(handle)
                if line.strip()
            ]


class TextExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        cleaned = re.sub(r"\s+", " ", str(item.get("text", ""))).strip()
        item["clean_text"] = cleaned
        return item


class Tokenizer(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        enriched = dict(item)
        enriched["tokens"] = re.findall(r"[\w\u4e00-\u9fff]+", item.get("clean_text", "").lower())
        return [enriched] if enriched["tokens"] else []


class SensitiveFilter(MapFunction):
    def __init__(self, sensitive_words: list[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.sensitive_words = sensitive_words or [
            "scam",
            "fraud",
            "hate",
            "violence",
            "诈骗",
            "仇恨",
            "暴力",
        ]

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("clean_text", "").lower()
        token_set = set(item.get("tokens", []))
        matches = [
            word
            for word in self.sensitive_words
            if word.lower() in text or word.lower() in token_set
        ]
        item["matched_terms"] = matches
        return item


class ViolationScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        matches = item.get("matched_terms", [])
        score = len(matches)
        item["violation_score"] = score
        item["action"] = "block" if score >= 2 else "review" if score == 1 else "allow"
        return item


class ModerationSink(SinkFunction):
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
