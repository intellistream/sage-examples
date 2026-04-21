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


def _parse_seconds(value: Any) -> float:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    parts = text.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    try:
        return float(text)
    except ValueError:
        return 0.0


class SubtitleSource(ListBatchSource):
    def __init__(self, subtitle_file: str, glossary_file: str, **kwargs):
        super().__init__(**kwargs)
        self.subtitle_file = subtitle_file
        self.glossary_file = glossary_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.subtitle_file)
        glossary = _load_records(self.glossary_file)
        glossary_map = {
            str(entry.get("term") or entry.get("source") or "").strip().lower(): str(
                entry.get("approved") or entry.get("target") or ""
            ).strip()
            for entry in glossary
            if str(entry.get("term") or entry.get("source") or "").strip()
        }
        for item in items:
            item.setdefault("app_slug", "subtitle_qc")
            item["glossary_map"] = glossary_map
            item.setdefault("source_path", self.subtitle_file)
        return items


class SubtitleBlockParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["start_seconds"] = _parse_seconds(payload.get("start") or payload.get("start_time"))
        payload["end_seconds"] = _parse_seconds(payload.get("end") or payload.get("end_time"))
        text = str(payload.get("text") or payload.get("subtitle") or "")
        payload["subtitle_text"] = text.strip()
        duration = max(payload["end_seconds"] - payload["start_seconds"], 0.0)
        payload["duration_seconds"] = round(duration, 2)
        payload["char_count"] = len(payload["subtitle_text"])
        return payload


class SubtitleGlossaryChecker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        text_lower = str(payload.get("subtitle_text") or "").lower()
        glossary_map = payload.get("glossary_map") or {}
        issues: list[str] = []
        matched_terms: list[str] = []
        for source_term, approved in glossary_map.items():
            if source_term and source_term in text_lower:
                matched_terms.append(source_term)
                if approved and approved.lower() not in text_lower:
                    issues.append(f"missing_approved_term:{source_term}->{approved}")
        payload["matched_glossary_terms"] = matched_terms
        payload["glossary_issues"] = issues
        return payload


class SubtitleTimingChecker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues = list(payload.get("glossary_issues") or [])
        duration = float(payload.get("duration_seconds") or 0.0)
        char_count = int(payload.get("char_count") or 0)
        cps = round(char_count / duration, 2) if duration > 0 else 999.0
        if duration <= 0:
            issues.append("invalid_time_range")
        if cps > 20:
            issues.append("reading_speed_too_fast")
        payload["reading_speed_cps"] = cps
        payload["qc_status"] = "fail" if issues else "pass"
        payload["qc_summary"] = (
            f"Block {payload.get('start_seconds')}-{payload.get('end_seconds')} status {payload.get('qc_status')}, "
            f"issues {', '.join(issues) or 'none'}."
        )
        return payload


class SubtitleQCSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("glossary_map", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
