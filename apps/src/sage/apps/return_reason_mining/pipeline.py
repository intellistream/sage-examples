from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import ReturnMiningSink, ReturnRecordSource, ReturnFeatureFusion, ReturnReasonClusterer, ReturnImprovementBuilder


def run_return_reason_mining_pipeline(return_file: str, output_file: str) -> None:
    env = LocalEnvironment('return_reason_mining')
    (
        env.from_batch(ReturnRecordSource, return_file=return_file)
        .map(ReturnFeatureFusion)
        .map(ReturnReasonClusterer)
        .map(ReturnImprovementBuilder)
        .sink(ReturnMiningSink, output_file=output_file)
    )
    env.submit(autostop=True)
