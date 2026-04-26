"""Voucher classifier pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ClassificationSink,
    FieldExtractor,
    OcrExtractor,
    RuleClassifier,
    VoucherSource,
)


def run_voucher_classifier_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("voucher_classifier")
    (
        env.from_batch(VoucherSource, input_file=input_file)
        .map(OcrExtractor)
        .map(FieldExtractor)
        .map(RuleClassifier)
        .sink(ClassificationSink, output_file=output_file)
    )
    env.submit(autostop=True)
