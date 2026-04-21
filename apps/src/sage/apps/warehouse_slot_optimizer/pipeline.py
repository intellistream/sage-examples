from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DistanceCostBuilder,
    PickingHistorySource,
    SlotHeatCalculator,
    SlotOptimizer,
    SlotPlanSink,
)


def run_warehouse_slot_optimizer_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("warehouse_slot_optimizer")
    (
        env.from_batch(PickingHistorySource, input_file=input_file)
        .map(SlotHeatCalculator)
        .map(DistanceCostBuilder)
        .map(SlotOptimizer)
        .sink(SlotPlanSink, output_file=output_file)
    )
    env.submit(autostop=True)
