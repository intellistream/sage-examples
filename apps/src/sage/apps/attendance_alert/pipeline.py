from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    AttendanceAlertSink,
    AttendanceAnomalyDetector,
    AttendanceSource,
    ScheduleMatcher,
)


def run_attendance_alert_pipeline(
    clock_file: str, output_file: str, schedule_file: str | None = None
) -> None:
    env = LocalEnvironment("attendance_alert")
    (
        env.from_batch(AttendanceSource, input_file=clock_file)
        .map(ScheduleMatcher, schedule_file=schedule_file)
        .map(AttendanceAnomalyDetector)
        .sink(AttendanceAlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
