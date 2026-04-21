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


class MailSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class MailParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        subject = str(item.get("subject") or "")
        body = str(item.get("body") or item.get("content") or "")
        item["mail_text"] = f"{subject} {body}".strip().lower()
        item["has_attachment"] = (
            str(item.get("attachment") or item.get("attachments") or "").strip() != ""
        )
        return item


class MailCategoryClassifier(MapFunction):
    RULES = {
        "support": {"ticket", "issue", "help", "error"},
        "finance": {"invoice", "payment", "budget", "reimbursement"},
        "hr": {"leave", "candidate", "training", "benefit"},
        "sales": {"proposal", "quote", "renewal", "deal"},
    }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("mail_text", "")
        scores = {
            label: sum(1 for term in terms if re.search(rf"\b{term}\b", text))
            for label, terms in self.RULES.items()
        }
        category, score = max(scores.items(), key=lambda pair: pair[1])
        item["mail_category"] = category if score > 0 else "general"
        return item


class MailPriorityScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("mail_text", "")
        score = 1 if item.get("has_attachment") else 0
        score += sum(1 for term in ("urgent", "asap", "immediately", "critical") if term in text)
        item["mail_priority"] = "high" if score >= 2 else "medium" if score == 1 else "low"
        return item


class MailSink(SinkFunction):
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
