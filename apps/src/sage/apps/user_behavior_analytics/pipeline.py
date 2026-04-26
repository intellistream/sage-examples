"""User behavior analytics pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import AnalyticsSink, EventNormalizer, EventSource, UserAggregator


def run_user_behavior_analytics_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("user_behavior_analytics")
    (
        env.from_batch(EventSource, input_file=input_file)
        .map(EventNormalizer)
        .map(UserAggregator)
        .sink(AnalyticsSink, output_file=output_file)
    )
    env.submit(autostop=True)
