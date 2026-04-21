from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    AidAlertSink,
    AidApplicationSource,
    AidGapDetector,
    AidRuleExtractor,
    StudentEligibilityMatcher,
)


def run_campus_aid_gap_alert_pipeline(
    application_file: str, profile_file: str, output_file: str
) -> None:
    env = LocalEnvironment("campus_aid_gap_alert")
    (
        env.from_batch(
            AidApplicationSource, application_file=application_file, profile_file=profile_file
        )
        .map(AidRuleExtractor)
        .map(StudentEligibilityMatcher)
        .map(AidGapDetector)
        .sink(AidAlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
