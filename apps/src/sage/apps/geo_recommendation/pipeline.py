from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import DistanceScorer, LocationSource, RecommendationFormatter, RecommendationSink


def run_geo_recommendation_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("geo_recommendation")
    (
        env.from_batch(LocationSource, input_file=input_file)
        .map(DistanceScorer)
        .map(RecommendationFormatter)
        .sink(RecommendationSink, output_file=output_file)
    )
    env.submit(autostop=True)
