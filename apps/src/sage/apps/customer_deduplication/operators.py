"""Operators for customer deduplication."""

from __future__ import annotations

import csv
import json
from difflib import SequenceMatcher
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class CustomerSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))


class SimilarityCalculator(MapFunction):
    def execute(self, row: dict[str, Any]) -> dict[str, Any]:
        name = (row.get("name") or "").strip().lower()
        email = (row.get("email") or "").strip().lower()
        phone = "".join(char for char in (row.get("phone") or "") if char.isdigit())
        row["fingerprint"] = "|".join([name, email, phone])
        return row


class DuplicateDetector(MapFunction):
    def __init__(self, threshold: float = 0.9, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold
        self.seen: list[dict[str, Any]] = []

    def execute(self, row: dict[str, Any]) -> dict[str, Any]:
        row["is_duplicate"] = False
        row["duplicate_of"] = ""
        row["similarity"] = 0.0
        fingerprint = row.get("fingerprint", "")
        for existing in self.seen:
            score = SequenceMatcher(None, fingerprint, existing.get("fingerprint", "")).ratio()
            if score >= self.threshold:
                row["is_duplicate"] = True
                row["duplicate_of"] = existing.get("customer_id") or existing.get("id") or ""
                row["similarity"] = round(score, 4)
                break
        self.seen.append(dict(row))
        return row


class DeduplicationSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.rows: list[dict[str, Any]] = []

    def execute(self, row: dict[str, Any]) -> None:
        self.rows.append(row)

    def teardown(self, context: Any) -> None:
        with open(self.output_file, "w", encoding="utf-8") as handle:
            json.dump(self.rows, handle, ensure_ascii=False, indent=2)
