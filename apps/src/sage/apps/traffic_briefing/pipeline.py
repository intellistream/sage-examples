from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    TrafficBriefFormatter,
    TrafficBriefSink,
    TrafficEventMerger,
    TrafficEventSource,
    TrafficImpactScorer,
)


def run_traffic_briefing_pipeline(event_file: str, output_file: str) -> None:
    env = LocalEnvironment("traffic_briefing")
    (
        env.from_batch(TrafficEventSource, event_file=event_file)
        .map(TrafficEventMerger)
        .map(TrafficImpactScorer)
        .map(TrafficBriefFormatter)
        .sink(TrafficBriefSink, output_file=output_file)
    )
    env.submit(autostop=True)
