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
    lines = [
        line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
    ]
    return [
        {"text": line, "line_number": index + 1, "source_path": str(path)}
        for index, line in enumerate(lines)
    ]


def _parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class BenchmarkSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_file)
        for item in items:
            item.setdefault("source_path", self.input_file)
        return items


class BenchmarkParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["benchmark_name"] = str(
            payload.get("benchmark_name") or payload.get("suite") or "unknown"
        )
        payload["model_name"] = str(payload.get("model_name") or payload.get("model") or "unknown")
        payload["current_score"] = _parse_float(
            payload.get("current_score") or payload.get("score")
        )
        payload["previous_score"] = _parse_float(
            payload.get("previous_score") or payload.get("last_score")
        )
        payload["rank"] = int(_parse_float(payload.get("rank") or 0))
        return payload


class BenchmarkDiffDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        delta = round(
            float(payload.get("current_score") or 0) - float(payload.get("previous_score") or 0), 4
        )
        payload["score_delta"] = delta
        if delta >= 2:
            change = "surge"
        elif delta <= -2:
            change = "drop"
        else:
            change = "stable"
        payload["change_type"] = change
        return payload


class BenchmarkTrendTagger(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        delta = float(payload.get("score_delta") or 0)
        rank = int(payload.get("rank") or 0)
        if delta <= -2 or rank >= 10:
            alert = "needs_attention"
        elif delta >= 2 and rank <= 3:
            alert = "leaderboard_gain"
        else:
            alert = "monitor"
        payload["trend_tag"] = alert
        payload["brief"] = (
            f"{payload.get('model_name')} 在 {payload.get('benchmark_name')} 上分数变化 {delta:+.2f}，"
            f"当前排名 {rank or 'N/A'}。"
        )
        return payload


class BenchmarkWatchSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
