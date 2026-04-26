from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class ExportQuerySource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class ExportFieldMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        mapped = {
            "record_id": item.get("record_id")
            or item.get("id")
            or item.get("query_id")
            or "unknown",
            "name": item.get("name") or item.get("title") or item.get("label") or "",
            "value": item.get("value") or item.get("amount") or item.get("score") or "",
        }
        item["export_record"] = mapped
        return item


class FormatTransformer(MapFunction):
    def __init__(self, output_format: str = "json", **kwargs):
        super().__init__(**kwargs)
        self.output_format = output_format.lower()

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        record = item.get("export_record", {})
        if self.output_format == "csv":
            item["transformed_payload"] = ",".join(
                str(record.get(field, "")) for field in ("record_id", "name", "value")
            )
        else:
            item["transformed_payload"] = json.dumps(record, ensure_ascii=False)
        item["output_format"] = self.output_format
        return item


class ExportSink(SinkFunction):
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
