from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    LabAlertSink,
    LabRecordSource,
    LabStageMapper,
    TurnaroundAnomalyDetector,
    TurnaroundTimeBuilder,
)


def run_lab_turnaround_alert_pipeline(record_file: str, output_file: str) -> None:
    env = LocalEnvironment("lab_turnaround_alert")
    (
        env.from_batch(LabRecordSource, record_file=record_file)
        .map(LabStageMapper)
        .map(TurnaroundTimeBuilder)
        .map(TurnaroundAnomalyDetector)
        .sink(LabAlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
