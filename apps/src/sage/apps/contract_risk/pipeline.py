"""Contract risk pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import ClauseSegmenter, ContractSource, RiskReportSink, RiskScorer, TextExtractor


def run_contract_risk_pipeline(
    input_path: str, output_file: str, rules: dict[str, int] | None = None
) -> None:
    env = LocalEnvironment("contract_risk")
    (
        env.from_batch(ContractSource, input_path=input_path)
        .map(TextExtractor)
        .flatmap(ClauseSegmenter)
        .map(RiskScorer, rules=rules)
        .sink(RiskReportSink, output_file=output_file)
    )
    env.submit(autostop=True)
