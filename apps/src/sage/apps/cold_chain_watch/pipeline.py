from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import ColdChainSink, ColdChainRecordSource, ColdChainBatchMatcher, TemperatureExcursionDetector, ColdChainRiskScorer


def run_cold_chain_watch_pipeline(record_file: str, output_file: str) -> None:
    env = LocalEnvironment('cold_chain_watch')
    (
        env.from_batch(ColdChainRecordSource, record_file=record_file)
        .map(ColdChainBatchMatcher)
        .map(TemperatureExcursionDetector)
        .map(ColdChainRiskScorer)
        .sink(ColdChainSink, output_file=output_file)
    )
    env.submit(autostop=True)
