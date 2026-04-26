from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class CompanySource(ListBatchSource):
    def __init__(self, company_file: str, **kwargs):
        super().__init__(**kwargs)
        self.company_file = company_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.company_file, encoding="utf-8", newline="") as handle:
            if self.company_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class CompanyInfoFetcher(MapFunction):
    def __init__(self, api_config: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.api_config = api_config

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["registered_years"] = int(float(item.get("registered_years") or 0))
        item["lawsuit_count"] = int(float(item.get("lawsuit_count") or 0))
        item["tax_score"] = float(item.get("tax_score") or 0)
        item["api_config"] = self.api_config or "local_rules"
        return item


class RiskFactorExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["risk_factor_count"] = int(item.get("lawsuit_count", 0)) + (
            1 if float(item.get("tax_score", 0)) < 60 else 0
        )
        return item


class CreditScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        score = (
            min(int(item.get("registered_years", 0)), 10)
            + float(item.get("tax_score", 0)) / 10
            - int(item.get("risk_factor_count", 0)) * 2
        )
        item["credit_score"] = round(score, 2)
        item["credit_level"] = "A" if score >= 12 else "B" if score >= 8 else "C"
        return item


class CreditReportSink(SinkFunction):
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
