from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class BackupSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class IncrementDetector(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        current_version = int(item.get("current_version") or item.get("version") or 0)
        last_synced_version = int(item.get("last_synced_version") or 0)
        item["has_increment"] = current_version > last_synced_version
        item["increment_size"] = max(current_version - last_synced_version, 0)
        return item


class BackupDispatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        target = item.get("target") or item.get("backup_target") or "secondary-storage"
        item["dispatch_plan"] = {
            "target": target,
            "mode": "incremental" if item.get("has_increment") else "skip",
        }
        return item


class ConsistencyChecker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        checksum = str(item.get("checksum") or "")
        remote_checksum = str(item.get("remote_checksum") or checksum)
        item["consistency_status"] = "consistent" if checksum == remote_checksum else "mismatch"
        return item


class BackupReportSink(SinkFunction):
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
