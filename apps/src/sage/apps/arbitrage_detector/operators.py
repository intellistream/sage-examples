from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class OrderSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class ExchangeRateFetcher(MapFunction):
    def __init__(self, static_rates: dict[str, float] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.static_rates = static_rates or {"USD/CNY": 7.2, "EUR/CNY": 7.8, "EUR/USD": 1.09}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        pair = f"{item.get('base_currency', 'USD')}/{item.get('quote_currency', 'CNY')}"
        item["rate"] = float(self.static_rates.get(pair, 1.0))
        return item


class ConversionCalculator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        amount = float(item.get("amount") or 0)
        item["converted_amount"] = round(amount * float(item.get("rate", 1.0)), 4)
        return item


class ArbitrageMatcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        market_rate = float(item.get("market_rate") or item.get("rate") or 1.0)
        delta = abs(float(item.get("rate", 1.0)) - market_rate)
        item["arbitrage_gap"] = round(delta, 6)
        item["has_opportunity"] = delta >= 0.02
        return item


class ArbitrageSink(SinkFunction):
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
