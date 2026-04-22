from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ApiAnalyticsSink,
    ApiAnomalyDetector,
    ApiLogParser,
    ApiLogSource,
    ApiMetricExtractor,
)


def run_api_log_analytics_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("api_log_analytics")
    (
        env.from_batch(ApiLogSource, input_file=input_file)
        .map(ApiLogParser)
        .map(ApiMetricExtractor)
        .map(ApiAnomalyDetector)
        .sink(ApiAnalyticsSink, output_file=output_file)
    )
    env.submit(autostop=True)
