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


class InvoiceSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class OrderSource(MapFunction):
    def __init__(self, order_file: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.order_file = order_file
        self._orders = _load_records(order_file) if order_file else []
        self._order_index = {
            str(
                order.get("order_id") or order.get("id") or order.get("invoice_order_id") or ""
            ).strip(): order
            for order in self._orders
        }

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        order_id = str(
            item.get("order_id")
            or item.get("invoice_order_id")
            or item.get("reference_order_id")
            or ""
        ).strip()
        item["linked_order"] = self._order_index.get(order_id, {})
        return item


class ReconciliationFieldNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["invoice_id"] = item.get("invoice_id") or item.get("id") or "unknown"
        item["order_id"] = str(item.get("order_id") or item.get("invoice_order_id") or "").strip()
        item["invoice_amount"] = round(
            float(item.get("invoice_amount") or item.get("amount") or 0), 2
        )
        linked_order = item.get("linked_order") or {}
        item["order_amount"] = round(
            float(linked_order.get("order_amount") or linked_order.get("amount") or 0), 2
        )
        return item


class InvoiceMatcher(MapFunction):
    def __init__(self, tolerance: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.tolerance = tolerance

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        delta = round(abs(item.get("invoice_amount", 0) - item.get("order_amount", 0)), 2)
        item["amount_delta"] = delta
        item["reconciliation_status"] = (
            "matched" if delta <= self.tolerance and item.get("linked_order") else "unmatched"
        )
        return item


class ReconciliationSink(SinkFunction):
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
