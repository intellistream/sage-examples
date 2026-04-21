from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    EvaluationFieldMapper,
    EvaluationNormalizer,
    VendorEvaluationSink,
    VendorEvaluationSource,
    VendorRiskMarker,
)


def run_vendor_evaluation_standardizer_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("vendor_evaluation_standardizer")
    (
        env.from_batch(VendorEvaluationSource, input_file=input_file)
        .map(EvaluationFieldMapper)
        .map(EvaluationNormalizer)
        .map(VendorRiskMarker)
        .sink(VendorEvaluationSink, output_file=output_file)
    )
    env.submit(autostop=True)
