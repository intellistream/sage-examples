from __future__ import annotations

import csv
import json
import re
from hashlib import sha1
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


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\-]{3,}", text.lower())


class KnowledgeArticleSource(ListBatchSource):
    def __init__(self, article_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.article_dir = article_dir

    def load_items(self) -> list[dict[str, str]]:
        items = _load_records(self.article_dir)
        for item in items:
            item.setdefault("app_slug", "knowledge_cleanup")
            item.setdefault("source_path", self.article_dir)
        return items


class KnowledgeFingerprintBuilder(MapFunction):
    def execute(self, item: dict[str, str]) -> dict[str, str | list[str]]:
        payload = dict(item)
        text = str(payload.get("text") or payload.get("content") or payload.get("body") or "")
        tokens = _tokenize(text)
        fingerprint_basis = " ".join(sorted(set(tokens[:40])))
        payload["fingerprint"] = sha1(fingerprint_basis.encode("utf-8")).hexdigest()[:12]
        payload["top_terms"] = sorted(set(tokens[:8]))
        payload["text_length"] = len(text)
        return payload


class KnowledgeDuplicateDetector(MapFunction):
    def execute(self, item: dict[str, str | list[str]]) -> dict[str, str | list[str] | int]:
        payload = dict(item)
        top_terms = payload.get("top_terms") or []
        source = Path(str(payload.get("source_path") or "")).name.lower()
        duplicate_signals = 0
        if len(top_terms) < 4:
            duplicate_signals += 1
        if "copy" in source or "duplicate" in source:
            duplicate_signals += 2
        payload["duplicate_risk_score"] = duplicate_signals
        payload["duplicate_status"] = (
            "likely_duplicate" if duplicate_signals >= 2 else "unique_or_needs_review"
        )
        return payload


class KnowledgeFreshnessScorer(MapFunction):
    def execute(self, item: dict[str, str | list[str] | int]) -> dict[str, str | list[str] | int]:
        payload = dict(item)
        updated_at = str(payload.get("updated_at") or payload.get("last_updated") or "")
        freshness_flags: list[str] = []
        if not updated_at:
            freshness_flags.append("missing_update_date")
        if int(payload.get("text_length") or 0) < 80:
            freshness_flags.append("thin_content")
        if str(payload.get("owner") or "").strip() == "":
            freshness_flags.append("missing_owner")
        payload["freshness_flags"] = freshness_flags
        payload["cleanup_priority"] = (
            "high"
            if freshness_flags or int(payload.get("duplicate_risk_score") or 0) >= 2
            else "normal"
        )
        payload["cleanup_summary"] = (
            f"Fingerprint {payload.get('fingerprint')}, duplicate status {payload.get('duplicate_status')}, "
            f"cleanup priority {payload.get('cleanup_priority')}."
        )
        return payload


class KnowledgeCleanupSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, object]] = []

    def execute(self, item: dict[str, object]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
