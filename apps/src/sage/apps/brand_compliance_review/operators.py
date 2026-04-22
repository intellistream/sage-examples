from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(path_str: str) -> list[dict[str, str]]:
    path = Path(path_str)
    if not path.exists():
        return [{"source_path": path_str, "text": path.name or path_str}]
    if path.is_dir():
        items: list[dict[str, str]] = []
        for child in sorted(path.iterdir()):
            if child.is_file():
                items.extend(_load_records(str(child)))
        return items
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {"value": str(item)} for item in data]
        if isinstance(data, dict):
            return [data]
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=delimiter))
    return [{"text": path.read_text(encoding="utf-8-sig"), "source_path": str(path)}]


class BrandAssetSource(ListBatchSource):
    def __init__(self, asset_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.asset_dir = asset_dir

    def load_items(self) -> list[dict[str, str]]:
        items = _load_records(self.asset_dir)
        for item in items:
            item.setdefault("app_slug", "brand_compliance_review")
            item.setdefault("source_path", self.asset_dir)
        return items


class BrandAssetParser(MapFunction):
    def execute(self, item: dict[str, str]) -> dict[str, str]:
        payload = dict(item)
        payload["title"] = str(payload.get("title") or "")
        payload["body"] = str(payload.get("body") or payload.get("text") or "")
        payload["asset_version"] = str(payload.get("asset_version") or payload.get("version") or "")
        payload["channel"] = str(payload.get("channel") or "generic")
        return payload


class BrandRuleMatcher(MapFunction):
    REQUIRED_TERMS = {"免责声明", "仅供参考", "official"}

    def execute(self, item: dict[str, str]) -> dict[str, str | list[str]]:
        payload = dict(item)
        text = f"{payload.get('title', '')} {payload.get('body', '')}".lower()
        issues: list[str] = []
        if "limited time" in text and "terms apply" not in text:
            issues.append("missing_campaign_disclaimer")
        if payload.get("asset_version", "") == "":
            issues.append("missing_asset_version")
        if re.search(r"\bfree\b", text) and "条件" not in payload.get("body", ""):
            issues.append("absolute_claim_without_condition")
        if "brandx" not in text:
            issues.append("missing_brand_name")
        payload["compliance_issues"] = issues
        payload["required_terms_present"] = [
            term for term in self.REQUIRED_TERMS if term.lower() in text
        ]
        return payload


class BrandRiskScorer(MapFunction):
    def execute(self, item: dict[str, str | list[str]]) -> dict[str, str | list[str] | int]:
        payload = dict(item)
        issue_count = len(payload.get("compliance_issues") or [])
        risk_level = "pass"
        if issue_count >= 3:
            risk_level = "high"
        elif issue_count >= 1:
            risk_level = "medium"
        payload["review_priority"] = risk_level
        payload["risk_score"] = issue_count * 25
        payload["review_summary"] = (
            f"Channel {payload.get('channel')} has {issue_count} compliance issues, "
            f"review priority {risk_level}."
        )
        return payload


class BrandReviewSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, object]] = []

    def execute(self, item: dict[str, object]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
