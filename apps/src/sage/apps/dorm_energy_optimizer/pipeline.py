from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import DormMapper, EnergyAdviceSink, EnergyAnomalyDetector, MeterSource


def run_dorm_energy_optimizer_pipeline(meter_file: str, output_file: str) -> None:
    env = LocalEnvironment("dorm_energy_optimizer")
    (
        env.from_batch(MeterSource, input_file=meter_file)
        .map(DormMapper)
        .map(EnergyAnomalyDetector)
        .sink(EnergyAdviceSink, output_file=output_file)
    )
    env.submit(autostop=True)
