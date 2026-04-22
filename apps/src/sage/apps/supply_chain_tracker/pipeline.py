from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DelayRiskDetector,
    StatusNormalizer,
    SupplyStatusSource,
    TimelineBuilder,
    TrackingSink,
)


def run_supply_chain_tracker_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("supply_chain_tracker")
    (
        env.from_batch(SupplyStatusSource, input_file=input_file)
        .map(StatusNormalizer)
        .map(TimelineBuilder)
        .map(DelayRiskDetector)
        .sink(TrackingSink, output_file=output_file)
    )
    env.submit(autostop=True)
