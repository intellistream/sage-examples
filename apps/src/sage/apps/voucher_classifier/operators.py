"""Operators for voucher classification."""

from __future__ import annotations

import csv
import json
import re
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class VoucherSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".csv"):
                return list(csv.DictReader(handle))
            return [{"raw_text": line.strip()} for line in handle if line.strip()]


class OcrExtractor(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        data["ocr_text"] = data.get("ocr_text") or data.get("raw_text") or ""
        return data


class FieldExtractor(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        text = data.get("ocr_text", "")
        amount_match = re.search(
            r"(?:amount|金额)\s*[:：]?\s*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE
        )
        date_match = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", text)
        category_hint = re.search(r"(travel|hotel|meal|office|taxi|fuel)", text, re.IGNORECASE)
        data["amount"] = float(amount_match.group(1)) if amount_match else 0.0
        data["voucher_date"] = date_match.group(1) if date_match else ""
        data["category_hint"] = category_hint.group(1) if category_hint else ""
        return data


class RuleClassifier(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        hint = str(data.get("category_hint", "")).lower()
        if hint in {"travel", "hotel", "taxi", "fuel"}:
            data["voucher_type"] = "travel_expense"
        elif hint in {"meal"}:
            data["voucher_type"] = "meal_expense"
        elif hint in {"office"}:
            data["voucher_type"] = "office_expense"
        else:
            data["voucher_type"] = "general_expense"
        return data


class ClassificationSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, data: dict[str, Any]) -> None:
        self.items.append(data)

    def teardown(self, context: Any) -> None:
        with open(self.output_file, "w", encoding="utf-8") as handle:
            json.dump(self.items, handle, ensure_ascii=False, indent=2)
