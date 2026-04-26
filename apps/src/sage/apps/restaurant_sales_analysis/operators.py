from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import FlatMapFunction, MapFunction, SinkFunction


class RestaurantOrderSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class DishSplitter(FlatMapFunction):
    def execute(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        dish_blob = str(item.get("dishes") or item.get("items") or "")
        if not dish_blob:
            return [dict(item)]

        dishes: list[dict[str, Any]] = []
        for raw_part in dish_blob.split("|"):
            part = raw_part.strip()
            if not part:
                continue
            pieces = [segment.strip() for segment in part.split(":")]
            dish_name = pieces[0]
            quantity = int(float(pieces[1])) if len(pieces) > 1 and pieces[1] else 1
            revenue = (
                float(pieces[2])
                if len(pieces) > 2 and pieces[2]
                else float(item.get("revenue") or 0)
            )
            cost = (
                float(pieces[3]) if len(pieces) > 3 and pieces[3] else float(item.get("cost") or 0)
            )
            dishes.append(
                {
                    "order_id": item.get("order_id") or item.get("id") or "",
                    "dish_name": dish_name,
                    "quantity": quantity,
                    "revenue": revenue,
                    "cost": cost,
                    "inventory_qty": item.get("inventory_qty") or item.get("stock_qty") or 0,
                    "waste_rate": item.get("waste_rate") or 0,
                    "sales_count": item.get("sales_count") or quantity,
                }
            )
        return dishes


class InventoryJoiner(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["inventory_qty"] = int(float(item.get("inventory_qty") or 0))
        item["waste_rate"] = float(item.get("waste_rate") or 0)
        return item


class MenuProfitScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        revenue = float(item.get("revenue") or 0)
        cost = float(item.get("cost") or 0)
        waste_penalty = float(item.get("waste_rate") or 0) * cost
        item["profit"] = round(revenue - cost - waste_penalty, 2)
        sales = int(float(item.get("sales_count") or item.get("quantity") or 0))
        inventory_qty = int(item.get("inventory_qty", 0))
        profit = float(item.get("profit", 0))
        if inventory_qty < 5 and sales >= 10:
            recommendation = "restock"
        elif profit > 30 and sales > 20:
            recommendation = "promote"
        elif profit <= 0:
            recommendation = "remove_or_reprice"
        else:
            recommendation = "keep"
        item["recommendation"] = recommendation
        return item


class MenuAdviceSink(SinkFunction):
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
