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
    lines = [
        line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
    ]
    return [
        {"text": line, "line_number": index + 1, "source_path": str(path)}
        for index, line in enumerate(lines)
    ]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower()))


class CourseDocSource(ListBatchSource):
    def __init__(self, doc_dir: str, question_file: str, **kwargs):
        super().__init__(**kwargs)
        self.doc_dir = doc_dir
        self.question_file = question_file

    def load_items(self) -> list[dict[str, Any]]:
        docs = _load_records(self.doc_dir)
        questions = _load_records(self.question_file)
        for item in docs:
            item["questions"] = questions
        return docs


class CourseChunker(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        payload = dict(item)
        text = str(payload.get("content") or payload.get("text") or payload.get("body") or "")
        parts = [part.strip() for part in re.split(r"[\n]+", text) if part.strip()]
        if not parts:
            parts = [text]
        results: list[dict[str, Any]] = []
        for index, part in enumerate(parts[:6]):
            child = dict(payload)
            child["chunk_id"] = index + 1
            child["chunk_text"] = part
            child["chunk_terms"] = sorted(_tokenize(part))
            results.append(child)
        return results


class CourseQuestionMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        chunk_terms = set(payload.get("chunk_terms") or [])
        best_question = None
        best_overlap: list[str] = []
        for question in payload.get("questions") or []:
            question_text = str(question.get("question") or question.get("text") or "")
            overlap = sorted(chunk_terms & _tokenize(question_text))
            if len(overlap) > len(best_overlap):
                best_overlap = overlap
                best_question = question_text
        payload["matched_question"] = best_question or ""
        payload["match_terms"] = best_overlap
        payload["match_score"] = len(best_overlap)
        return payload


class CourseAnswerFormatter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        chunk_text = str(payload.get("chunk_text") or "")
        answer = chunk_text[:180].strip()
        if len(chunk_text) > 180:
            answer += "..."
        payload["answer_excerpt"] = answer
        payload["answer_status"] = (
            "answered" if payload.get("match_score") else "needs_manual_review"
        )
        return payload


class CourseAnswerSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("questions", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
