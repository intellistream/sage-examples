"""Operators for matching contract templates."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class RequirementSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = Path(input_file)

    def load_items(self) -> list[dict[str, Any]]:
        text = self.input_file.read_text(encoding="utf-8")
        if self.input_file.suffix.lower() == ".json":
            payload = json.loads(text)
            if isinstance(payload, list):
                return payload
        return [
            {"requirement_id": "1", "text": line.strip()}
            for line in text.splitlines()
            if line.strip()
        ]


class KeywordExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", item.get("text", "").lower())
        item["keywords"] = [token for token in tokens if len(token) > 1]
        return item


class TemplateMatcher(MapFunction):
    def __init__(self, template_file: str | None = None, top_k: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.template_file = template_file
        self.top_k = top_k
        self.templates = self._load_templates(template_file)

    def _load_templates(self, template_file: str | None) -> list[dict[str, Any]]:
        if template_file:
            path = Path(template_file)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        return [
            {
                "template_id": "employment",
                "name": "Employment Contract",
                "text": "labor employment confidentiality compensation termination",
            },
            {
                "template_id": "nda",
                "name": "Non Disclosure Agreement",
                "text": "confidential information disclosure secrecy obligation remedy",
            },
            {
                "template_id": "service",
                "name": "Service Agreement",
                "text": "service scope payment delivery acceptance liability support",
            },
        ]

    def _score(self, req_tokens: list[str], template_text: str) -> float:
        req_counts = Counter(req_tokens)
        tpl_counts = Counter(re.findall(r"[\w\u4e00-\u9fff]+", template_text.lower()))
        common = set(req_counts) & set(tpl_counts)
        numerator = sum(req_counts[token] * tpl_counts[token] for token in common)
        left = math.sqrt(sum(value * value for value in req_counts.values()))
        right = math.sqrt(sum(value * value for value in tpl_counts.values()))
        if not left or not right:
            return 0.0
        return round(numerator / (left * right), 4)

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        matches = []
        req_tokens = item.get("keywords", [])
        for template in self.templates:
            matches.append(
                {
                    "template_id": template["template_id"],
                    "name": template["name"],
                    "score": self._score(req_tokens, template.get("text", "")),
                }
            )
        item["matches"] = sorted(matches, key=lambda value: value["score"], reverse=True)[
            : self.top_k
        ]
        return item


class MatchSink(SinkFunction):
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
