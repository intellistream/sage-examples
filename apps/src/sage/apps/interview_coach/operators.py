from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


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


class InterviewAnswerSource(ListBatchSource):
    def __init__(self, answer_file: str, rubric_file: str, **kwargs):
        super().__init__(**kwargs)
        self.answer_file = answer_file
        self.rubric_file = rubric_file

    def load_items(self) -> list[dict[str, Any]]:
        answers = _load_records(self.answer_file)
        rubric = _load_records(self.rubric_file)
        for item in answers:
            item["rubric"] = rubric
        return answers


class InterviewQuestionMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        question = str(payload.get("question") or payload.get("prompt") or "")
        answer = str(payload.get("answer") or payload.get("text") or "")
        payload["question_terms"] = sorted(_tokenize(question))
        payload["answer_terms"] = sorted(_tokenize(answer))
        payload["uses_star_structure"] = all(
            marker in answer.lower() for marker in ("situation", "task", "action", "result")
        )
        return payload


class InterviewScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = 0
        if payload.get("uses_star_structure"):
            score += 4
        if len(payload.get("answer_terms") or []) >= 12:
            score += 3
        if any(char.isdigit() for char in str(payload.get("answer") or "")):
            score += 2
        rubric_hits = 0
        answer_terms = set(payload.get("answer_terms") or [])
        for criterion in payload.get("rubric") or []:
            if answer_terms & _tokenize(
                str(criterion.get("criterion") or criterion.get("text") or "")
            ):
                rubric_hits += 1
        payload["rubric_hits"] = rubric_hits
        payload["interview_score"] = score + rubric_hits
        payload["performance_level"] = "strong" if payload["interview_score"] >= 8 else "developing"
        return payload


class InterviewAdviceBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        advice: list[str] = []
        if not payload.get("uses_star_structure"):
            advice.append("补齐 Situation/Task/Action/Result 结构。")
        if payload.get("rubric_hits", 0) < 2:
            advice.append("多覆盖岗位 rubric 中的关键能力点。")
        if not any(char.isdigit() for char in str(payload.get("answer") or "")):
            advice.append("补充量化结果，增强说服力。")
        payload["coaching_advice"] = advice or ["回答结构较完整，可继续打磨表达精炼度。"]
        return payload


class InterviewReportSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("rubric", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
