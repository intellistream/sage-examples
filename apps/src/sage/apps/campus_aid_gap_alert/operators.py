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


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[,;|]", str(value or "")) if part.strip()]


def _parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class AidApplicationSource(ListBatchSource):
    def __init__(self, application_file: str, profile_file: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.application_file = application_file
        self.profile_file = profile_file or ""

    def load_items(self) -> list[dict[str, Any]]:
        applications = _load_records(self.application_file)
        profiles = _load_records(self.profile_file) if self.profile_file else []
        profile_index = {
            str(
                profile.get("student_id") or profile.get("id") or profile.get("student") or ""
            ): profile
            for profile in profiles
        }
        for item in applications:
            student_id = str(item.get("student_id") or item.get("id") or item.get("student") or "")
            item.setdefault("app_slug", "campus_aid_gap_alert")
            item["student_profile"] = profile_index.get(student_id, {})
            item.setdefault("source_path", self.application_file)
        return applications


class AidRuleExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["required_docs"] = _as_list(
            payload.get("required_docs") or payload.get("documents_required")
        )
        payload["submitted_docs"] = _as_list(
            payload.get("submitted_docs") or payload.get("submitted_materials")
        )
        payload["min_gpa"] = _parse_float(payload.get("min_gpa"), 0.0)
        payload["deadline_days"] = int(_parse_float(payload.get("deadline_days"), 999))
        payload["hardship_required"] = str(payload.get("aid_type") or "").lower() in {
            "grant",
            "subsidy",
        }
        return payload


class StudentEligibilityMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        profile = payload.get("student_profile") or {}
        gpa = _parse_float(profile.get("gpa") or payload.get("gpa"), 0.0)
        household_income = _parse_float(profile.get("household_income") or 0, 0.0)
        discipline_flag = str(profile.get("disciplinary_action") or "").strip().lower() in {
            "true",
            "yes",
            "1",
        }
        missing_docs = sorted(
            set(payload.get("required_docs") or []) - set(payload.get("submitted_docs") or [])
        )
        issues: list[str] = []
        if gpa < payload.get("min_gpa", 0.0):
            issues.append("gpa_below_requirement")
        if payload.get("hardship_required") and household_income > 40000:
            issues.append("income_above_hardship_threshold")
        if discipline_flag:
            issues.append("disciplinary_record_present")
        payload["student_id"] = str(
            profile.get("student_id") or payload.get("student_id") or "unknown"
        )
        payload["student_gpa"] = gpa
        payload["missing_docs"] = missing_docs
        payload["eligibility_issues"] = issues
        return payload


class AidGapDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = (
            len(payload.get("missing_docs") or []) * 2
            + len(payload.get("eligibility_issues") or []) * 3
        )
        if int(payload.get("deadline_days") or 999) <= 7:
            score += 3
        elif int(payload.get("deadline_days") or 999) <= 14:
            score += 1
        alert_level = "watch"
        if score >= 8:
            alert_level = "critical"
        elif score >= 4:
            alert_level = "action_required"
        payload["gap_score"] = score
        payload["alert_level"] = alert_level
        payload["alert_summary"] = (
            f"学生 {payload.get('student_id')} 缺少 {len(payload.get('missing_docs') or [])} 份材料，"
            f"资格问题 {len(payload.get('eligibility_issues') or [])} 项，预警级别 {alert_level}。"
        )
        return payload


class AidAlertSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("student_profile", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
