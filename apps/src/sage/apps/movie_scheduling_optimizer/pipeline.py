from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import HeatScorer, ScheduleSink, ScreeningSource, SlotOptimizer


def run_movie_scheduling_optimizer_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("movie_scheduling_optimizer")
    (
        env.from_batch(ScreeningSource, input_file=input_file)
        .map(HeatScorer)
        .map(SlotOptimizer)
        .sink(ScheduleSink, output_file=output_file)
    )
    env.submit(autostop=True)
