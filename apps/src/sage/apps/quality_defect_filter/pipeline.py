"""Quality defect filter pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DefectSeverityScorer,
    DefectSink,
    DefectSplitter,
    DefectStandardizer,
    DefectTextExtractor,
    QualityReportSource,
)


def run_quality_defect_filter_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("quality_defect_filter")
    (
        env.from_batch(QualityReportSource, input_file=input_file)
        .map(DefectTextExtractor)
        .flatmap(DefectSplitter)
        .map(DefectStandardizer)
        .map(DefectSeverityScorer)
        .sink(DefectSink, output_file=output_file)
    )
    env.submit(autostop=True)
