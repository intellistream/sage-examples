from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class PropertySource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class NearbyListingFetcher(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["area_sqm"] = float(item.get("area_sqm") or 0)
        item["price_per_sqm"] = float(
            item.get("price_per_sqm") or item.get("nearby_avg_price") or 0
        )
        item["location_factor"] = float(item.get("location_factor") or 1)
        item["listing_count"] = int(
            float(item.get("listing_count") or item.get("comps_count") or 0)
        )
        return item


class ValueFeatureExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["area_sqm"] = float(item.get("area_sqm") or 0)
        item["price_per_sqm"] = float(item.get("price_per_sqm") or 0)
        item["location_factor"] = float(item.get("location_factor") or 1)
        return item


class ValuationFeatureBuilder(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        enriched = NearbyListingFetcher().execute(item)
        enriched["market_confidence"] = min(1.0, 0.5 + enriched["listing_count"] * 0.05)
        return enriched


class ValueEstimator(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["estimated_value"] = round(
            item["area_sqm"] * item["price_per_sqm"] * item["location_factor"], 2
        )
        return item


class ValuationCalculator(ValueEstimator):
    pass


class ValuationSink(SinkFunction):
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
