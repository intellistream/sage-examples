from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


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


class PodcastTranscriptSource(ListBatchSource):
    def __init__(self, transcript_file: str, **kwargs):
        super().__init__(**kwargs)
        self.transcript_file = transcript_file

    def load_items(self) -> list[dict[str, str]]:
        items = _load_records(self.transcript_file)
        for item in items:
            item.setdefault("app_slug", "podcast_highlight")
            item.setdefault("source_path", self.transcript_file)
        return items


class PodcastSegmenter(FlatMapFunction):
    def execute(self, item: dict[str, str]) -> list[dict[str, str | int]]:
        text = str(item.get("transcript") or item.get("text") or "")
        parts = [part.strip() for part in re.split(r"\n\s*\n|\|", text) if part.strip()]
        if not parts:
            parts = [json.dumps(item, ensure_ascii=False)]
        results: list[dict[str, str | int]] = []
        for index, part in enumerate(parts[:8]):
            child = dict(item)
            child["segment_text"] = part
            child["segment_index"] = index
            time_match = re.search(r"\[(\d{2}:\d{2})-(\d{2}:\d{2})\]", part)
            child["segment_range"] = time_match.group(0) if time_match else f"segment-{index}"
            results.append(child)
        return results


class HighlightScorer(MapFunction):
    HIGH_SIGNAL_TERMS = {
        "surprising",
        "lesson",
        "mistake",
        "growth",
        "turning point",
        "breakthrough",
    }

    def execute(self, item: dict[str, str | int]) -> dict[str, str | int | float]:
        payload = dict(item)
        segment = str(payload.get("segment_text") or "")
        score = len(segment.split()) / 8
        lowered = segment.lower()
        for term in self.HIGH_SIGNAL_TERMS:
            if term in lowered:
                score += 3
        if "?" in segment:
            score += 1
        payload["highlight_score"] = round(score, 2)
        payload["highlight_tag"] = "viral_candidate" if score >= 6 else "usable_clip"
        return payload


class HighlightTitleBuilder(MapFunction):
    def execute(self, item: dict[str, str | int | float]) -> dict[str, str | int | float]:
        payload = dict(item)
        segment = re.sub(r"\[[^\]]+\]\s*", "", str(payload.get("segment_text") or "")).strip()
        words = segment.split()
        title = " ".join(words[:8]) if words else "Podcast Highlight"
        payload["highlight_title"] = title[:80]
        payload["distribution_note"] = (
            f"Segment {payload.get('segment_range')} scored {payload.get('highlight_score')}, "
            f"recommended tag {payload.get('highlight_tag')}."
        )
        return payload


class HighlightSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, object]] = []

    def execute(self, item: dict[str, object]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
