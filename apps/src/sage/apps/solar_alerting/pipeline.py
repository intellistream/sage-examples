from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    SolarAlertSink,
    SolarAnomalyDetector,
    SolarPriorityScorer,
    SolarSignalSource,
    SolarWeatherJoiner,
)


def run_solar_alerting_pipeline(sensor_file: str, weather_file: str, output_file: str) -> None:
    env = LocalEnvironment("solar_alerting")
    (
        env.from_batch(SolarSignalSource, sensor_file=sensor_file, weather_file=weather_file)
        .map(SolarWeatherJoiner)
        .map(SolarAnomalyDetector)
        .map(SolarPriorityScorer)
        .sink(SolarAlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
