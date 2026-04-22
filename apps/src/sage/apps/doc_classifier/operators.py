"""Operators for rule-based document classification."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class DocSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".csv"):
                rows = list(csv.DictReader(handle))
                return [
                    {"doc_id": row.get("doc_id", ""), "text": row.get("text", "")} for row in rows
                ]
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return [
                {"doc_id": str(index + 1), "text": line.strip()}
                for index, line in enumerate(handle)
                if line.strip()
            ]


class TextExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["clean_text"] = " ".join(str(item.get("text", "")).split())
        return item


class Tokenizer(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", item.get("clean_text", "").lower())
        enriched = dict(item)
        enriched["tokens"] = tokens
        return [enriched] if tokens else []


class FeatureExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        tokens = item.get("tokens") or re.findall(
            r"[\w\u4e00-\u9fff]+", item.get("clean_text", "").lower()
        )
        counts = Counter(tokens)
        item["token_count"] = len(tokens)
        item["top_terms"] = [term for term, _ in counts.most_common(5)]
        total = max(len(tokens), 1)
        item["tfidf_features"] = {term: round(count / total, 4) for term, count in counts.items()}
        return item


class Classifier(MapFunction):
    def __init__(self, label_rules: dict[str, list[str]] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.label_rules = label_rules or {
            "contract": ["contract", "agreement", "clause", "terms"],
            "invoice": ["invoice", "vat", "payment", "tax"],
            "resume": ["resume", "experience", "education", "skills"],
            "report": ["report", "summary", "analysis", "findings"],
        }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("clean_text", "").lower()
        best_label = "other"
        best_score = 0
        for label, keywords in self.label_rules.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score > best_score:
                best_score = score
                best_label = label
        item["label"] = best_label
        item["label_score"] = best_score
        return item


class DocSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        with open(self.output_file, "w", encoding="utf-8") as handle:
            json.dump(self.items, handle, ensure_ascii=False, indent=2)
