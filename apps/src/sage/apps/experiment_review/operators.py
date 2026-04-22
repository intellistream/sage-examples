from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


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


def _parse_float(value: Any) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return float(match.group(0)) if match else None


class ExperimentLogSource(ListBatchSource):
    def __init__(self, log_file: str, **kwargs):
        super().__init__(**kwargs)
        self.log_file = log_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.log_file)
        for item in items:
            item.setdefault("source_path", self.log_file)
        return items


class ExperimentStepSplitter(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        payload = dict(item)
        raw_text = str(payload.get("log_text") or payload.get("steps") or payload.get("text") or "")
        parts = [part.strip() for part in re.split(r"[\n;|]+", raw_text) if part.strip()]
        results: list[dict[str, Any]] = []
        for index, part in enumerate(parts or [raw_text]):
            child = dict(payload)
            child["step_index"] = index + 1
            child["step_text"] = part.strip()
            results.append(child)
        return results


class ExperimentParameterExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        step_text = str(payload.get("step_text") or "")
        temperature = (
            _parse_float(
                re.search(r"temp(?:erature)?[^\d-]*(-?\d+(?:\.\d+)?)", step_text, re.I).group(1)
            )
            if re.search(r"temp(?:erature)?[^\d-]*(-?\d+(?:\.\d+)?)", step_text, re.I)
            else None
        )
        ph_value = (
            _parse_float(re.search(r"pH[^\d-]*(-?\d+(?:\.\d+)?)", step_text, re.I).group(1))
            if re.search(r"pH[^\d-]*(-?\d+(?:\.\d+)?)", step_text, re.I)
            else None
        )
        yield_value = (
            _parse_float(re.search(r"yield[^\d-]*(-?\d+(?:\.\d+)?)", step_text, re.I).group(1))
            if re.search(r"yield[^\d-]*(-?\d+(?:\.\d+)?)", step_text, re.I)
            else None
        )
        payload["temperature_c"] = temperature
        payload["ph_value"] = ph_value
        payload["yield_percent"] = yield_value
        payload["step_tags"] = [
            tag
            for tag, marker in (
                ("incubation", "incubat"),
                ("wash", "wash"),
                ("centrifuge", "centrif"),
                ("mix", "mix"),
            )
            if marker in step_text.lower()
        ]
        return payload


class ExperimentAnomalyMarker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        reasons: list[str] = []
        temperature = payload.get("temperature_c")
        ph_value = payload.get("ph_value")
        yield_percent = payload.get("yield_percent")
        step_text = str(payload.get("step_text") or "").lower()
        if temperature is not None and not 2 <= float(temperature) <= 40:
            reasons.append("temperature_out_of_range")
        if ph_value is not None and not 5 <= float(ph_value) <= 9:
            reasons.append("ph_out_of_range")
        if yield_percent is not None and float(yield_percent) < 60:
            reasons.append("yield_drop")
        if any(
            marker in step_text for marker in ("contamination", "failed", "repeat", "unexpected")
        ):
            reasons.append("manual_flag")
        payload["anomaly_reasons"] = reasons
        payload["review_status"] = "needs_review" if reasons else "normal"
        return payload


class ExperimentReviewSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
