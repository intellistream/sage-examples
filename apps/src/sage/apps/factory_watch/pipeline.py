from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import SensorWatchSink, SensorSource, SensorDeviceMapper, SensorAnomalyScorer, SensorAlertLeveler


def run_factory_watch_pipeline(sensor_file: str, output_file: str) -> None:
    env = LocalEnvironment('factory_watch')
    (
        env.from_batch(SensorSource, sensor_file=sensor_file)
        .map(SensorDeviceMapper)
        .map(SensorAnomalyScorer)
        .map(SensorAlertLeveler)
        .sink(SensorWatchSink, output_file=output_file)
    )
    env.submit(autostop=True)
