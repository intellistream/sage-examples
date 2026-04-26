from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CertificationGapDetector,
    CourseNormalizer,
    EmployeeMapper,
    LearningProfileSink,
    LearningRecordSource,
)


def run_learning_record_hub_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("learning_record_hub")
    (
        env.from_batch(LearningRecordSource, input_file=input_file)
        .map(EmployeeMapper)
        .map(CourseNormalizer)
        .map(CertificationGapDetector)
        .sink(LearningProfileSink, output_file=output_file)
    )
    env.submit(autostop=True)
