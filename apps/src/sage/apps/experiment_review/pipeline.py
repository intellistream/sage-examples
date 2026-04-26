from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ExperimentAnomalyMarker,
    ExperimentLogSource,
    ExperimentParameterExtractor,
    ExperimentReviewSink,
    ExperimentStepSplitter,
)


def run_experiment_review_pipeline(log_file: str, output_file: str) -> None:
    env = LocalEnvironment("experiment_review")
    (
        env.from_batch(ExperimentLogSource, log_file=log_file)
        .flatmap(ExperimentStepSplitter)
        .map(ExperimentParameterExtractor)
        .map(ExperimentAnomalyMarker)
        .sink(ExperimentReviewSink, output_file=output_file)
    )
    env.submit(autostop=True)
