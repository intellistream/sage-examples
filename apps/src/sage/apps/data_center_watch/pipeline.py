from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CapacityCoolingScorer,
    DataCenterMetricSource,
    DataCenterRiskMarker,
    DataCenterWatchSink,
    RackMapper,
)


def run_data_center_watch_pipeline(metric_file: str, alert_file: str, output_file: str) -> None:
    env = LocalEnvironment('data_center_watch')
    (
        env.from_batch(DataCenterMetricSource, metric_file=metric_file, alert_file=alert_file)
        .map(RackMapper)
        .map(CapacityCoolingScorer)
        .map(DataCenterRiskMarker)
        .sink(DataCenterWatchSink, output_file=output_file)
    )
    env.submit(autostop=True)
