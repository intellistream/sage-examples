"""Operators for product synchronization."""

from __future__ import annotations

import csv
import json
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class ProductSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class FieldMapper(MapFunction):
    def __init__(self, field_map: dict[str, str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.field_map = field_map or {
            "sku": "sku",
            "name": "title",
            "price": "price",
            "inventory": "stock",
            "category": "category",
        }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        mapped = {}
        for source_key, target_key in self.field_map.items():
            mapped[target_key] = item.get(source_key, "")
        mapped["raw"] = item
        return mapped


class DataValidator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        errors = []
        if not item.get("sku"):
            errors.append("missing_sku")
        if not item.get("title"):
            errors.append("missing_title")
        try:
            item["price"] = float(item.get("price") or 0)
        except (TypeError, ValueError):
            errors.append("invalid_price")
            item["price"] = 0.0
        try:
            item["stock"] = int(float(item.get("stock") or 0))
        except (TypeError, ValueError):
            errors.append("invalid_stock")
            item["stock"] = 0
        item["is_valid"] = not errors
        item["validation_errors"] = errors
        return item


class PlatformSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        with open(self.output_file, "w", encoding="utf-8") as handle:
            json.dump(self.items, handle, ensure_ascii=False, indent=2)
