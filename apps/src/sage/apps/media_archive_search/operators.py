from __future__ import annotations

import csv
import json
import re
from hashlib import sha1
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


class MediaAssetSource(ListBatchSource):
    def __init__(self, asset_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.asset_dir = asset_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.asset_dir)
        for item in items:
            item.setdefault("app_slug", "media_archive_search")
            item.setdefault("source_path", self.asset_dir)
        return items


class MediaMetadataExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["asset_title"] = str(payload.get("title") or payload.get("filename") or "untitled")
        payload["asset_type"] = str(payload.get("asset_type") or payload.get("type") or "document")
        payload["people"] = str(payload.get("people") or payload.get("speaker") or "")
        payload["event_date"] = str(payload.get("event_date") or payload.get("date") or "")
        text = str(
            payload.get("text") or payload.get("description") or payload.get("summary") or ""
        )
        payload["metadata_fingerprint"] = sha1(text.lower().encode("utf-8")).hexdigest()[:12]
        payload["text_length"] = len(text)
        return payload


class MediaTagger(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        text = str(payload.get("text") or payload.get("description") or "").lower()
        tags = []
        for term in ("launch", "interview", "product", "conference", "customer"):
            if term in text:
                tags.append(term)
        if not tags:
            tags.append(str(payload.get("asset_type") or "general"))
        payload["media_tags"] = tags
        payload["search_key"] = f"{payload.get('asset_title')}|{'/'.join(tags)}"
        return payload


class MediaDuplicateDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        duplicate_signals: list[str] = []
        source_name = Path(str(payload.get("source_path") or "")).name.lower()
        if "copy" in source_name or "final_final" in source_name:
            duplicate_signals.append("filename_duplicate_pattern")
        if int(payload.get("text_length") or 0) < 40:
            duplicate_signals.append("insufficient_metadata")
        payload["duplicate_signals"] = duplicate_signals
        payload["archive_status"] = "review_duplicate" if duplicate_signals else "index_ready"
        payload["archive_summary"] = (
            f"Asset {payload.get('asset_title')} status {payload.get('archive_status')}, "
            f"tags {', '.join(payload.get('media_tags') or [])}."
        )
        return payload


class MediaArchiveSink(SinkFunction):
    def __init__(self, output_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_dir
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.mkdir(parents=True, exist_ok=True)
        (target / "results.json").write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
