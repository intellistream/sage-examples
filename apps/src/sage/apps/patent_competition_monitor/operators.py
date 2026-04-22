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
    return {token for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[,;|]", str(value or "")) if part.strip()]


class PatentSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_file)
        for item in items:
            item.setdefault("source_path", self.input_file)
        return items


class PatentFieldExtractor(MapFunction):
    TECH_FIELDS = {
        "semiconductor": {"chip", "semiconductor", "wafer", "packaging"},
        "biotech": {"protein", "gene", "antibody", "biomarker"},
        "battery": {"battery", "cathode", "electrolyte", "anode"},
        "ai": {"model", "neural", "inference", "training", "llm"},
        "network": {"router", "wireless", "5g", "network", "antenna"},
    }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        title = str(
            payload.get("title") or payload.get("patent_title") or payload.get("text") or ""
        )
        abstract = str(payload.get("abstract") or payload.get("summary") or "")
        claims = str(payload.get("claims") or payload.get("claim_summary") or "")
        combined = " ".join(part for part in (title, abstract, claims) if part)
        tokens = _tokenize(combined)
        field_scores = {
            field: sum(1 for keyword in keywords if keyword in tokens)
            for field, keywords in self.TECH_FIELDS.items()
        }
        best_field, best_score = max(
            field_scores.items(), key=lambda pair: pair[1], default=("general", 0)
        )
        payload["patent_title"] = title
        payload["patent_field"] = best_field if best_score > 0 else "general"
        payload["assignee"] = str(payload.get("assignee") or payload.get("applicant") or "unknown")
        payload["monitored_company"] = str(
            payload.get("monitored_company") or payload.get("target_company") or ""
        )
        payload["key_terms"] = sorted(tokens)[:12]
        return payload


class PatentTopicClassifier(MapFunction):
    RISK_TERMS = {
        "high": {"exclusive", "infringement", "blocking", "cease", "litigation"},
        "medium": {"claim", "patent", "priority", "licensing", "portfolio"},
    }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        title = str(payload.get("patent_title") or "")
        tokens = set(payload.get("key_terms") or []) | _tokenize(title)
        monitored_terms = _tokenize(
            str(payload.get("monitored_terms") or payload.get("watch_terms") or "")
        )
        overlap_terms = sorted(tokens & monitored_terms)
        cited_competitors = _as_list(
            payload.get("cited_competitors") or payload.get("competitors") or ""
        )
        monitored_company = str(payload.get("monitored_company") or "").strip().lower()
        competitor_hit = any(name.lower() != monitored_company for name in cited_competitors)
        severity = "low"
        if overlap_terms or any(term in tokens for term in self.RISK_TERMS["high"]):
            severity = "high"
        elif competitor_hit or any(term in tokens for term in self.RISK_TERMS["medium"]):
            severity = "medium"
        payload["watch_term_overlap"] = overlap_terms
        payload["competitor_hit"] = competitor_hit
        payload["risk_severity"] = severity
        payload["topic_label"] = f"{payload.get('patent_field', 'general')}_{severity}"
        return payload


class CompetitorAggregator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        overlap_count = len(payload.get("watch_term_overlap") or [])
        competitor_bonus = 3 if payload.get("competitor_hit") else 0
        claim_width = min(
            len(_tokenize(str(payload.get("claims") or payload.get("claim_summary") or ""))), 8
        )
        score = overlap_count * 2 + competitor_bonus + claim_width
        level = "watch"
        if score >= 10:
            level = "critical"
        elif score >= 6:
            level = "elevated"
        payload["infringement_risk_score"] = score
        payload["alert_level"] = level
        payload["alert_summary"] = (
            f"{payload.get('assignee', 'unknown')} 在 {payload.get('patent_field', 'general')} 领域出现 {level} 风险，"
            f"命中 {overlap_count} 个关注术语。"
        )
        return payload


class PatentDigestSink(SinkFunction):
    def __init__(self, output_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_dir
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        else:
            target.mkdir(parents=True, exist_ok=True)
            (target / "results.json").write_text(
                json.dumps(self.items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
