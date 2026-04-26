from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ComplianceDocClassifier,
    ComplianceDocSource,
    ComplianceReminderSink,
    ReviewDeadlineChecker,
)


def run_compliance_doc_manager_pipeline(
    input_file: str, output_file: str, reference_date: str | None = None
) -> None:
    env = LocalEnvironment("compliance_doc_manager")
    (
        env.from_batch(ComplianceDocSource, input_file=input_file)
        .map(ComplianceDocClassifier)
        .map(ReviewDeadlineChecker, reference_date=reference_date)
        .sink(ComplianceReminderSink, output_file=output_file)
    )
    env.submit(autostop=True)
