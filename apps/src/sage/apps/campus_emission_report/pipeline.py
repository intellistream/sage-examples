from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CampusEmissionAggregator,
    CampusEmissionSource,
    CampusReportFormatter,
    CampusReportSink,
    EmissionFactorMapper,
)


def run_campus_emission_report_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment('campus_emission_report')
    (
        env.from_batch(CampusEmissionSource, input_dir=input_dir)
        .map(EmissionFactorMapper)
        .map(CampusEmissionAggregator)
        .map(CampusReportFormatter)
        .sink(CampusReportSink, output_file=output_file)
    )
    env.submit(autostop=True)
