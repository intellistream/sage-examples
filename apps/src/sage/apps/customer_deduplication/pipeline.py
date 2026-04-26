"""Customer deduplication pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import CustomerSource, DeduplicationSink, DuplicateDetector, SimilarityCalculator


def run_customer_deduplication_pipeline(
    input_file: str,
    output_file: str,
    threshold: float = 0.9,
) -> None:
    env = LocalEnvironment("customer_deduplication")
    (
        env.from_batch(CustomerSource, input_file=input_file)
        .map(SimilarityCalculator)
        .map(DuplicateDetector, threshold=threshold)
        .sink(DeduplicationSink, output_file=output_file)
    )
    env.submit(autostop=True)
