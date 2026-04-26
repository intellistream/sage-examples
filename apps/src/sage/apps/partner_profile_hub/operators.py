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


class PartnerSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class PartnerFieldMapper(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["partner_id"] = (
            item.get("partner_id") or item.get("id") or item.get("crm_id") or "unknown"
        )
        item["partner_name"] = (
            item.get("partner_name") or item.get("name") or item.get("company") or "unknown"
        )
        item["partner_email"] = str(item.get("partner_email") or item.get("email") or "").lower()
        item["partner_phone"] = str(item.get("partner_phone") or item.get("phone") or "")
        item["partner_region"] = (
            item.get("partner_region") or item.get("region") or item.get("country") or "unknown"
        )
        return item


class PartnerDeduplicator(MapFunction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._seen_keys: set[str] = set()

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        dedup_key = "|".join(
            [
                str(item.get("partner_name", "")).strip().lower(),
                str(item.get("partner_email", "")).strip().lower(),
                str(item.get("partner_phone", "")).strip(),
            ]
        )
        item["partner_dedup_key"] = dedup_key
        item["is_duplicate"] = dedup_key in self._seen_keys
        self._seen_keys.add(dedup_key)
        return item


class PartnerProfileBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["partner_profile"] = {
            "partner_id": item.get("partner_id"),
            "partner_name": item.get("partner_name"),
            "region": item.get("partner_region"),
            "contact": {
                "email": item.get("partner_email"),
                "phone": item.get("partner_phone"),
            },
            "duplicate_status": "duplicate" if item.get("is_duplicate") else "primary",
        }
        return item


class PartnerSink(SinkFunction):
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
