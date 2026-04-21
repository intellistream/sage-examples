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


class PaperSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class PaperKeywordExtractor(MapFunction):
    def __init__(self, top_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.top_k = top_k

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            str(item.get(field, "")) for field in ("title", "abstract", "keywords", "content")
        ).lower()
        tokens = re.findall(r"[a-z]{4,}", text)
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        item["paper_keywords"] = [
            token
            for token, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[
                : self.top_k
            ]
        ]
        return item


class PaperTopicClassifier(MapFunction):
    TOPIC_RULES = {
        "biology": {"cell", "gene", "biomarker", "protein", "clinical", "medical"},
        "computer_science": {"model", "algorithm", "dataset", "learning", "neural", "system"},
        "finance": {"market", "trading", "risk", "asset", "price", "credit"},
        "policy": {"policy", "regulation", "governance", "compliance", "public"},
    }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        keywords = {keyword.lower() for keyword in item.get("paper_keywords", [])}
        text = " ".join(str(item.get(field, "")) for field in ("title", "abstract")).lower()
        scores = {
            topic: sum(1 for term in terms if term in keywords or term in text)
            for topic, terms in self.TOPIC_RULES.items()
        }
        topic, score = max(scores.items(), key=lambda pair: pair[1])
        item["paper_topic"] = topic if score > 0 else "general"
        item["paper_label"] = f"{item['paper_topic']}_paper"
        return item


class PaperClassificationSink(SinkFunction):
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
