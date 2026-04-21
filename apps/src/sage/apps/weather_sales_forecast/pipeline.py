from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    RestockSuggestionSink,
    SalesForecaster,
    SalesHistorySource,
    WeatherFetcher,
    WeatherSalesFeatureBuilder,
)


def run_weather_sales_forecast_pipeline(
    sales_file: str,
    output_file: str,
    city_config: str | None = None,
    weather_map: dict[str, float] | None = None,
) -> None:
    env = LocalEnvironment("weather_sales_forecast")
    (
        env.from_batch(SalesHistorySource, input_file=sales_file)
        .map(WeatherFetcher, weather_map=weather_map)
        .map(WeatherSalesFeatureBuilder)
        .map(SalesForecaster)
        .sink(RestockSuggestionSink, output_file=output_file)
    )
    env.submit(autostop=True)
