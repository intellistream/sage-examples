"""Order anomaly detector pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import AnomalySink, FeatureCalculator, OrderSource, RuleScorer


def run_order_anomaly_detector_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("order_anomaly_detector")
    (
        env.from_batch(OrderSource, input_file=input_file)
        .map(FeatureCalculator)
        .map(RuleScorer)
        .sink(AnomalySink, output_file=output_file)
    )
    env.submit(autostop=True)
