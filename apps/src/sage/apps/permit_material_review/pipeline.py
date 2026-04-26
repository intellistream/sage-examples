from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    PermitChecklistChecker,
    PermitDocumentClassifier,
    PermitMaterialSource,
    PermitReviewFormatter,
    PermitReviewSink,
)


def run_permit_material_review_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment("permit_material_review")
    (
        env.from_batch(PermitMaterialSource, input_dir=input_dir)
        .map(PermitDocumentClassifier)
        .map(PermitChecklistChecker)
        .map(PermitReviewFormatter)
        .sink(PermitReviewSink, output_file=output_file)
    )
    env.submit(autostop=True)
