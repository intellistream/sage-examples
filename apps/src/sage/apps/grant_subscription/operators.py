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


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


class GrantAnnouncementSource(ListBatchSource):
    def __init__(self, announcement_file: str, profile_file: str, **kwargs):
        super().__init__(**kwargs)
        self.announcement_file = announcement_file
        self.profile_file = profile_file

    def load_items(self) -> list[dict[str, Any]]:
        announcements = _load_records(self.announcement_file)
        profiles = _load_records(self.profile_file)
        for item in announcements:
            item["team_profiles"] = profiles
        return announcements


class GrantRuleExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        call_text = " ".join(
            str(payload.get(field, ""))
            for field in ("title", "summary", "focus_area", "eligibility", "keywords")
        )
        tokens = _tokenize(call_text)
        payload["grant_id"] = str(
            payload.get("grant_id") or payload.get("id") or payload.get("title") or "grant"
        )
        payload["matched_topics"] = sorted(tokens)[:15]
        payload["deadline_days"] = _parse_int(
            payload.get("deadline_days") or payload.get("days_left"), 999
        )
        payload["budget_amount"] = _parse_int(
            payload.get("budget_amount") or payload.get("budget") or 0, 0
        )
        payload["eligibility_flags"] = {
            "industry_only": "industry" in tokens,
            "phd_required": "phd" in tokens,
            "international": "international" in tokens,
        }
        return payload


class TeamProfileMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        matched_topics = set(payload.get("matched_topics") or [])
        ranked_matches: list[dict[str, Any]] = []
        for profile in payload.get("team_profiles") or []:
            interests = _tokenize(
                " ".join(
                    str(profile.get(field, ""))
                    for field in ("research_focus", "keywords", "strengths")
                )
            )
            overlap = sorted(matched_topics & interests)
            if not overlap:
                continue
            team_size = _parse_int(profile.get("team_size") or 0)
            score = len(overlap) * 3 + min(team_size, 8)
            ranked_matches.append(
                {
                    "team": profile.get("team")
                    or profile.get("lab")
                    or profile.get("name")
                    or "unknown",
                    "overlap_terms": overlap,
                    "match_score": score,
                }
            )
        ranked_matches.sort(key=lambda entry: (-entry["match_score"], entry["team"]))
        payload["recommended_teams"] = ranked_matches[:3]
        return payload


class GrantPriorityScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        team_score = (
            payload.get("recommended_teams", [{}])[0].get("match_score", 0)
            if payload.get("recommended_teams")
            else 0
        )
        urgency_bonus = 4 if int(payload.get("deadline_days") or 999) <= 14 else 1
        budget_bonus = 3 if int(payload.get("budget_amount") or 0) >= 500000 else 1
        priority_score = int(team_score) + urgency_bonus + budget_bonus
        priority = "watch"
        if priority_score >= 12:
            priority = "high"
        elif priority_score >= 7:
            priority = "medium"
        payload["priority_score"] = priority_score
        payload["priority_level"] = priority
        payload["dispatch_summary"] = (
            f"{payload.get('grant_id')} 推荐 {len(payload.get('recommended_teams') or [])} 个团队，"
            f"优先级 {priority}。"
        )
        return payload


class GrantAlertSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("team_profiles", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
