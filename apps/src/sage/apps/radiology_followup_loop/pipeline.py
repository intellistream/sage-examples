from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    FollowupDeadlineChecker,
    FollowupExtractor,
    FollowupSink,
    PatientMatcher,
    RadiologyReportSource,
)


def run_radiology_followup_loop_pipeline(report_file: str, patient_file: str, output_file: str) -> None:
    env = LocalEnvironment('radiology_followup_loop')
    (
        env.from_batch(RadiologyReportSource, report_file=report_file, patient_file=patient_file)
        .map(FollowupExtractor)
        .map(PatientMatcher)
        .map(FollowupDeadlineChecker)
        .sink(FollowupSink, output_file=output_file)
    )
    env.submit(autostop=True)
