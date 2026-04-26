from __future__ import annotations

import csv
import json
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
    return [{"text": path.read_text(encoding="utf-8-sig"), "source_path": str(path)}]


class PermitMaterialSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "permit_material_review")
            item.setdefault("source_path", self.input_dir)
        return items


class PermitDocumentClassifier(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["application_type"] = str(
            payload.get("application_type") or payload.get("permit_type") or "general"
        )
        payload["document_type"] = str(
            payload.get("document_type") or payload.get("filename") or "unknown"
        )
        payload["submitted_docs"] = [
            part.strip()
            for part in str(payload.get("submitted_docs") or "").split(",")
            if part.strip()
        ]
        return payload


class PermitChecklistChecker(MapFunction):
    CHECKLISTS = {
        "construction": ["application_form", "site_plan", "safety_commitment"],
        "food": ["application_form", "health_certificate", "floor_plan"],
    }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        required = self.CHECKLISTS.get(
            str(payload.get("application_type") or ""), ["application_form", "id_copy"]
        )
        submitted = set(payload.get("submitted_docs") or [])
        missing = [doc for doc in required if doc not in submitted]
        issues = list(missing)
        if str(payload.get("has_stamp") or "false").lower() not in {"true", "1", "yes"}:
            issues.append("missing_stamp")
        if int(float(payload.get("page_count") or 0)) == 0:
            issues.append("missing_pages")
        payload["required_docs"] = required
        payload["missing_items"] = missing
        payload["review_issues"] = issues
        return payload


class PermitReviewFormatter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        status = "return_for_fix" if payload.get("review_issues") else "accepted"
        payload["review_status"] = status
        payload["review_summary"] = (
            f"Application {payload.get('application_type')} status {status}, "
            f"issues {', '.join(payload.get('review_issues') or []) or 'none'}."
        )
        return payload


class PermitReviewSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
