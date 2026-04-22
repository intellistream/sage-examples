from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CongestionDetector,
    HeatmapSink,
    HeatScoreCalculator,
    VisitorFlowSource,
    ZoneMapper,
)


def run_exhibition_heatmap_pipeline(flow_file: str, output_file: str) -> None:
    env = LocalEnvironment("exhibition_heatmap")
    (
        env.from_batch(VisitorFlowSource, flow_file=flow_file)
        .map(ZoneMapper)
        .map(HeatScoreCalculator)
        .map(CongestionDetector)
        .sink(HeatmapSink, output_file=output_file)
    )
    env.submit(autostop=True)
