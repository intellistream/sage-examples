from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CompetitorAggregator,
    PatentDigestSink,
    PatentFieldExtractor,
    PatentSource,
    PatentTopicClassifier,
)


def run_patent_competition_monitor_pipeline(input_file: str, output_dir: str) -> None:
    env = LocalEnvironment("patent_competition_monitor")
    (
        env.from_batch(PatentSource, input_file=input_file)
        .map(PatentFieldExtractor)
        .map(PatentTopicClassifier)
        .map(CompetitorAggregator)
        .sink(PatentDigestSink, output_dir=output_dir)
    )
    env.submit(autostop=True)
