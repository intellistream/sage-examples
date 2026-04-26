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


class AssignmentDraftSource(ListBatchSource):
    def __init__(self, draft_file: str, rubric_file: str, **kwargs):
        super().__init__(**kwargs)
        self.draft_file = draft_file
        self.rubric_file = rubric_file

    def load_items(self) -> list[dict[str, Any]]:
        drafts = _load_records(self.draft_file)
        rubric = _load_records(self.rubric_file)
        for item in drafts:
            item["rubric"] = rubric
        return drafts


class AssignmentSectionParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        draft_text = str(
            payload.get("draft") or payload.get("content") or payload.get("text") or ""
        )
        sections = [
            section.strip() for section in re.split(r"[\n]{2,}", draft_text) if section.strip()
        ]
        payload["section_count"] = len(sections) or 1
        payload["word_count"] = len(re.findall(r"\w+", draft_text))
        payload["draft_terms"] = sorted(_tokenize(draft_text))
        return payload


class RubricMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        draft_terms = set(payload.get("draft_terms") or [])
        matched: list[dict[str, Any]] = []
        for criterion in payload.get("rubric") or []:
            criterion_text = str(criterion.get("criterion") or criterion.get("text") or "")
            overlap = sorted(draft_terms & _tokenize(criterion_text))
            matched.append(
                {
                    "criterion": criterion_text,
                    "matched_terms": overlap,
                    "covered": bool(overlap),
                }
            )
        payload["rubric_matches"] = matched
        payload["coverage_ratio"] = (
            sum(1 for item in matched if item["covered"]) / len(matched) if matched else 0.0
        )
        return payload


class FeedbackComposer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        suggestions: list[str] = []
        if payload.get("word_count", 0) < 120:
            suggestions.append("补充论证细节，正文偏短。")
        if payload.get("section_count", 0) < 3:
            suggestions.append("建议增加更清晰的分段结构。")
        uncovered = [
            entry["criterion"]
            for entry in payload.get("rubric_matches", [])
            if not entry["covered"]
        ]
        if uncovered:
            suggestions.append(f"未明显覆盖评分点：{'; '.join(uncovered[:3])}。")
        payload["feedback_level"] = "good" if payload.get("coverage_ratio", 0) >= 0.6 else "revise"
        payload["feedback_comments"] = suggestions or ["结构完整，可进入教师复核。"]
        return payload


class AssignmentFeedbackSink(SinkFunction):
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
