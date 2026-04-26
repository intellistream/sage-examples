from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class ContentSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class ContentCleaner(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(str(item.get(field, "")) for field in ("title", "content", "summary"))
        item["cleaned_text"] = re.sub(r"\s+", " ", text).strip().lower()
        return item


class TagCandidateExtractor(MapFunction):
    def __init__(self, top_k: int = 8, **kwargs):
        super().__init__(**kwargs)
        self.top_k = top_k

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        tokens = re.findall(r"[a-z]{4,}", item.get("cleaned_text", ""))
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        item["tag_candidates"] = [
            token
            for token, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[
                : self.top_k
            ]
        ]
        return item


class TagSelector(MapFunction):
    RULE_TAGS = {
        "finance": {"invoice", "budget", "cash", "profit", "revenue"},
        "hr": {"employee", "training", "attendance", "recruitment"},
        "compliance": {"audit", "policy", "regulation", "control"},
        "technology": {"api", "cloud", "model", "platform", "system"},
    }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        candidates = set(item.get("tag_candidates", []))
        selected_tags = [tag for tag, words in self.RULE_TAGS.items() if candidates & words]
        item["selected_tags"] = selected_tags or item.get("tag_candidates", [])[:3]
        return item


class TagSink(SinkFunction):
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
