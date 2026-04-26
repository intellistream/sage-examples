from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class ApiLogSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class ApiLogParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        raw = str(item.get("log") or item.get("message") or "")
        status_match = re.search(r"\b(\d{3})\b", raw)
        latency_match = re.search(r"(\d+(?:\.\d+)?)ms", raw.lower())
        item["status_code"] = (
            int(status_match.group(1)) if status_match else int(item.get("status_code") or 200)
        )
        item["latency_ms"] = (
            float(latency_match.group(1)) if latency_match else float(item.get("latency_ms") or 0)
        )
        item["endpoint"] = item.get("endpoint") or item.get("path") or "/unknown"
        return item


class ApiMetricExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        latency = float(item.get("latency_ms") or 0)
        status_code = int(item.get("status_code") or 200)
        item["api_metric"] = {
            "endpoint": item.get("endpoint"),
            "latency_bucket": "slow" if latency >= 800 else "normal",
            "is_error": status_code >= 500,
        }
        return item


class ApiAnomalyDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        metric = item.get("api_metric", {})
        item["api_anomaly"] = bool(metric.get("is_error") or metric.get("latency_bucket") == "slow")
        item["api_anomaly_reason"] = (
            "server_error"
            if metric.get("is_error")
            else "slow_request"
            if metric.get("latency_bucket") == "slow"
            else "normal"
        )
        return item


class ApiAnalyticsSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        Path(self.output_file).write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
