from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ClimateAnomalyDetector,
    GreenhouseAdviceBuilder,
    GreenhouseSensorSource,
    GreenhouseSink,
    GreenhouseZoneMapper,
)


def run_greenhouse_assistant_pipeline(sensor_file: str, task_file: str, output_file: str) -> None:
    env = LocalEnvironment('greenhouse_assistant')
    (
        env.from_batch(GreenhouseSensorSource, sensor_file=sensor_file, task_file=task_file)
        .map(GreenhouseZoneMapper)
        .map(ClimateAnomalyDetector)
        .map(GreenhouseAdviceBuilder)
        .sink(GreenhouseSink, output_file=output_file)
    )
    env.submit(autostop=True)
