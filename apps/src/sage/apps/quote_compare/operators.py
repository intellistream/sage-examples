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
    return [{"text": path.read_text(encoding="utf-8-sig"), "source_path": str(path)}]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class QuoteSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "quote_compare")
            item.setdefault("source_path", self.input_dir)
        return items


class QuoteNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        unit_price = _to_float(
            payload.get("unit_price") or payload.get("price") or payload.get("quoted_price")
        )
        quantity = _to_float(payload.get("quantity") or 1, 1.0)
        lead_days = _to_float(payload.get("lead_days") or payload.get("delivery_days"), 999)
        payload["vendor"] = str(payload.get("vendor") or payload.get("supplier") or "unknown")
        payload["currency"] = str(payload.get("currency") or "CNY")
        payload["unit_price"] = unit_price
        payload["quantity"] = quantity
        payload["lead_days"] = lead_days
        payload["total_cost"] = round(unit_price * quantity, 2)
        return payload


class QuoteConditionComparer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        warranty_months = _to_float(payload.get("warranty_months"), 0)
        risk_flags: list[str] = []
        if payload.get("lead_days", 999) > 14:
            risk_flags.append("long_lead_time")
        if warranty_months < 12:
            risk_flags.append("short_warranty")
        if str(payload.get("payment_terms") or "").lower() in {"100% prepay", "full prepayment"}:
            risk_flags.append("aggressive_payment_terms")
        payload["warranty_months"] = warranty_months
        payload["risk_flags"] = risk_flags
        return payload


class QuoteScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = 100.0
        score -= payload.get("total_cost", 0.0) / 1000
        score -= max(payload.get("lead_days", 0.0) - 7, 0) * 1.5
        score -= len(payload.get("risk_flags") or []) * 8
        recommendation = "preferred"
        if score < 70:
            recommendation = "review_required"
        if score < 50:
            recommendation = "high_risk"
        payload["quote_score"] = round(score, 2)
        payload["recommendation"] = recommendation
        payload["comparison_summary"] = (
            f"Vendor {payload.get('vendor')} total cost {payload.get('total_cost')} {payload.get('currency')}, "
            f"lead time {payload.get('lead_days')} days, recommendation {recommendation}."
        )
        return payload


class QuoteCompareSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
