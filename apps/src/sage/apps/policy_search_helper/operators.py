from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


def _load_records(path_str: str) -> list[dict[str, Any]]:
    path = Path(path_str)
    if not path.exists():
        return [{"source_path": path_str, "text": path.name or path_str}]
    if path.is_dir():
        items: list[dict[str, Any]] = []
        for child in sorted(path.iterdir()):
            if child.is_file():
                items.extend(_load_records(str(child)))
        return items
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {"value": item} for item in data]
        if isinstance(data, dict):
            return [data]
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=delimiter))
    return [{"text": path.read_text(encoding="utf-8-sig"), "source_path": str(path)}]


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[\w\-]{2,}", text.lower()) if token}


class PolicyDocSource(ListBatchSource):
    def __init__(self, doc_dir: str, question_file: str, **kwargs):
        super().__init__(**kwargs)
        self.doc_dir = doc_dir
        self.question_file = question_file

    def load_items(self) -> list[dict[str, Any]]:
        questions = _load_records(self.question_file)
        question_text = "\n".join(
            str(item.get("question") or item.get("text") or "") for item in questions
        )
        items = _load_records(self.doc_dir)
        for item in items:
            item.setdefault("app_slug", "policy_search_helper")
            item["question_text"] = question_text
            item["question_file"] = self.question_file
        return items


class PolicyChunker(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        text = str(item.get("text") or item.get("content") or item.get("body") or "")
        parts = [
            part.strip() for part in re.split(r"\n\s*\n|(?<=。)|(?<=\.)\s+", text) if part.strip()
        ]
        if not parts:
            parts = [json.dumps(item, ensure_ascii=False)]
        results: list[dict[str, Any]] = []
        for index, part in enumerate(parts[:8]):
            child = dict(item)
            child["policy_chunk"] = part
            child["chunk_index"] = index
            results.append(child)
        return results


class PolicyQuestionMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        question_text = str(payload.get("question_text") or "")
        chunk = str(payload.get("policy_chunk") or "")
        overlap = _tokenize(question_text) & _tokenize(chunk)
        payload["matched_terms"] = sorted(overlap)
        payload["match_score"] = len(overlap)
        payload["matched_clause"] = chunk
        return payload


class PolicyAnswerComposer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        source = Path(str(payload.get("source_path") or "")).name
        clause = str(payload.get("matched_clause") or "")
        payload["answer_excerpt"] = clause[:220]
        payload["citation"] = f"{source}#chunk-{payload.get('chunk_index', 0)}"
        payload["answer_quality"] = "direct" if payload.get("match_score", 0) >= 2 else "weak"
        payload["answer_summary"] = (
            f"Matched clause from {source}, citation {payload.get('citation')}, "
            f"matched terms {', '.join(payload.get('matched_terms') or []) or 'none'}."
        )
        return payload


class PolicyAnswerSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
