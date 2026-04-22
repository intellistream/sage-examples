from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


class SalesSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class SalesHistorySource(SalesSource):
    pass


class WeatherJoiner(MapFunction):
    def __init__(self, weather_map: dict[str, float] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.weather_map = weather_map or {"sunny": 1.1, "cloudy": 1.0, "rainy": 0.85, "snowy": 0.7}

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        weather = str(data.get("weather") or "cloudy").lower()
        data["weather_factor"] = self.weather_map.get(weather, 1.0)
        return data


class WeatherFetcher(WeatherJoiner):
    pass


class WeatherSalesFeatureBuilder(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        baseline = float(data.get("baseline_sales") or data.get("sales") or 0)
        data["baseline_sales"] = baseline
        data["weather_adjusted_baseline"] = round(
            baseline * float(data.get("weather_factor", 1.0)), 2
        )
        return data


class ForecastCalculator(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        baseline = float(data.get("baseline_sales") or data.get("sales") or 0)
        forecast = baseline * float(data.get("weather_factor", 1.0))
        data["forecast_sales"] = round(forecast, 2)
        return data


class SalesForecaster(ForecastCalculator):
    pass


class ForecastSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, data: dict[str, Any]) -> None:
        self.items.append(data)

    def teardown(self, context: Any) -> None:
        Path(self.output_file).write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )


class RestockSuggestionSink(ForecastSink):
    pass
