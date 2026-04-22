"""News aggregator pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DeduplicationFilter,
    FingerprintCalculator,
    NewsExtractor,
    NewsSink,
    RssSource,
)


def run_news_aggregator_pipeline(source_file: str, output_file: str) -> None:
    env = LocalEnvironment("news_aggregator")
    (
        env.from_batch(RssSource, source_file=source_file)
        .map(NewsExtractor)
        .map(FingerprintCalculator)
        .map(DeduplicationFilter)
        .sink(NewsSink, output_file=output_file)
    )
    env.submit(autostop=True)
