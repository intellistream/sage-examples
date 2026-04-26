from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CommunityEventSource,
    CommunityInsightSink,
    CommunityTopicAggregator,
    CommunityZoneMapper,
    HotspotDriftDetector,
)


def run_community_hotspot_drift_pipeline(event_file: str, output_file: str) -> None:
    env = LocalEnvironment("community_hotspot_drift")
    (
        env.from_batch(CommunityEventSource, event_file=event_file)
        .map(CommunityZoneMapper)
        .map(CommunityTopicAggregator)
        .map(HotspotDriftDetector)
        .sink(CommunityInsightSink, output_file=output_file)
    )
    env.submit(autostop=True)
