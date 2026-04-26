"""Operators for RSS aggregation and deduplication."""

from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class RssSource(ListBatchSource):
    def __init__(self, source_file: str, **kwargs):
        super().__init__(**kwargs)
        self.source_file = source_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.source_file, encoding="utf-8", newline="") as handle:
            if self.source_file.lower().endswith(".csv"):
                return [
                    {"feed": row.get("feed", "")}
                    for row in csv.DictReader(handle)
                    if row.get("feed")
                ]
            return [{"feed": line.strip()} for line in handle if line.strip()]


class NewsExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        feed = item.get("feed", "")
        if feed.startswith("http"):
            payload = urlopen(feed, timeout=10).read().decode("utf-8", errors="ignore")
        else:
            payload = Path(feed).read_text(encoding="utf-8")
        root = ET.fromstring(payload)
        entries = []
        for entry in (
            root.findall(".//item")[:20]
            + root.findall(".//{http://www.w3.org/2005/Atom}entry")[:20]
        ):
            title = self._text(entry, "title")
            link = self._text(entry, "link") or (
                entry.find("link").attrib.get("href", "") if entry.find("link") is not None else ""
            )
            summary = self._text(entry, "description") or self._text(entry, "summary")
            if title:
                entries.append({"title": title, "link": link, "summary": summary})
        item["entries"] = entries
        return item

    def _text(self, entry: ET.Element, name: str) -> str:
        node = entry.find(name)
        if node is None:
            node = entry.find(f"{{http://www.w3.org/2005/Atom}}{name}")
        return (node.text or "").strip() if node is not None and node.text else ""


class FingerprintCalculator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = []
        for entry in item.get("entries", []):
            text = f"{entry.get('title', '')}|{entry.get('summary', '')}".lower().strip()
            entry["fingerprint"] = hashlib.md5(text.encode("utf-8")).hexdigest()
            normalized.append(entry)
        item["entries"] = normalized
        return item


class DeduplicationFilter(MapFunction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seen: set[str] = set()

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        unique_entries = []
        for entry in item.get("entries", []):
            fingerprint = entry.get("fingerprint", "")
            if fingerprint and fingerprint not in self.seen:
                self.seen.add(fingerprint)
                unique_entries.append(entry)
        item["entries"] = unique_entries
        return item


class NewsSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.extend(item.get("entries", []))

    def teardown(self, context: Any) -> None:
        Path(self.output_file).write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
