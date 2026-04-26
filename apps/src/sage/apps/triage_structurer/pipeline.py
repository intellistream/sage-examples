from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    TriageFieldExtractor,
    TriagePriorityAssigner,
    TriageRecordSource,
    TriageSink,
    TriageSummaryBuilder,
)


def run_triage_structurer_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment('triage_structurer')
    (
        env.from_batch(TriageRecordSource, input_file=input_file)
        .map(TriageFieldExtractor)
        .map(TriagePriorityAssigner)
        .map(TriageSummaryBuilder)
        .sink(TriageSink, output_file=output_file)
    )
    env.submit(autostop=True)
