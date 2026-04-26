from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CashflowFeatureBuilder,
    CashflowForecaster,
    CashflowRiskMarker,
    CashflowSink,
    CashflowSource,
)


def run_cashflow_watch_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment('cashflow_watch')
    (
        env.from_batch(CashflowSource, input_dir=input_dir)
        .map(CashflowFeatureBuilder)
        .map(CashflowForecaster)
        .map(CashflowRiskMarker)
        .sink(CashflowSink, output_file=output_file)
    )
    env.submit(autostop=True)
