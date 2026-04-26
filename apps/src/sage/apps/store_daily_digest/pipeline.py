from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    StoreActionBuilder,
    StoreDigestSink,
    StoreExceptionDetector,
    StoreMetricAggregator,
    StoreOpsSource,
)


def run_store_daily_digest_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment("store_daily_digest")
    (
        env.from_batch(StoreOpsSource, input_dir=input_dir)
        .map(StoreMetricAggregator)
        .map(StoreExceptionDetector)
        .map(StoreActionBuilder)
        .sink(StoreDigestSink, output_file=output_file)
    )
    env.submit(autostop=True)
