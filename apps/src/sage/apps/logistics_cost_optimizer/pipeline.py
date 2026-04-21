from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import CostCalculator, LogisticsSink, OptionSelector, ShipmentSource


def run_logistics_cost_optimizer_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("logistics_cost_optimizer")
    (
        env.from_batch(ShipmentSource, input_file=input_file)
        .map(CostCalculator)
        .map(OptionSelector)
        .sink(LogisticsSink, output_file=output_file)
    )
    env.submit(autostop=True)
