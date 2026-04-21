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


class CampaignPlanSource(ListBatchSource):
    def __init__(self, plan_file: str, channel_file: str, **kwargs):
        super().__init__(**kwargs)
        self.plan_file = plan_file
        self.channel_file = channel_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.plan_file)
        channels = _load_records(self.channel_file)
        channel_index = {str(item.get("channel") or ""): item for item in channels}
        for item in items:
            channel = str(item.get("channel") or "")
            item.setdefault("app_slug", "content_scheduler")
            item["channel_rules"] = channel_index.get(channel, {})
            item.setdefault("source_path", self.plan_file)
        return items


class ChannelRuleMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        rules = payload.get("channel_rules") or {}
        payload["channel"] = str(payload.get("channel") or rules.get("channel") or "general")
        payload["max_posts_per_week"] = int(rules.get("max_posts_per_week") or 7)
        payload["blackout_dates"] = str(rules.get("blackout_dates") or "")
        payload["preferred_format"] = str(rules.get("preferred_format") or "post")
        return payload


class TopicAllocator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        theme = str(payload.get("theme") or payload.get("campaign_theme") or "general")
        publish_date = str(payload.get("publish_date") or payload.get("date") or "")
        audience = str(payload.get("audience") or "general")
        payload["scheduled_topic"] = f"{theme}-{audience}".strip("-")
        payload["suggested_asset_type"] = payload.get("preferred_format") or "post"
        payload["schedule_slot"] = f"{payload.get('channel')}@{publish_date or 'tbd'}"
        return payload


class ScheduleConflictDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        issues: list[str] = []
        topic = str(payload.get("scheduled_topic") or "")
        publish_date = str(payload.get("publish_date") or payload.get("date") or "")
        blackout = str(payload.get("blackout_dates") or "")
        if publish_date and publish_date in blackout:
            issues.append("blackout_date_conflict")
        if topic.count("launch") > 1 or topic.count("sale") > 1:
            issues.append("duplicate_campaign_theme")
        if int(payload.get("planned_posts_this_week") or 1) > int(
            payload.get("max_posts_per_week") or 7
        ):
            issues.append("channel_capacity_exceeded")
        payload["schedule_conflicts"] = issues
        payload["schedule_status"] = "needs_review" if issues else "ready"
        payload["schedule_summary"] = (
            f"Slot {payload.get('schedule_slot')} topic {topic}, conflicts {', '.join(issues) or 'none'}."
        )
        return payload


class ContentScheduleSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        payload = dict(item)
        payload.pop("channel_rules", None)
        self.items.append(payload)
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
