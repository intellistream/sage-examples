from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import CreditAggregator, CreditResultSink, FactorCollector, UserCreditSource


def run_multi_factor_credit_score_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("multi_factor_credit_score")
    (
        env.from_batch(UserCreditSource, input_file=input_file)
        .map(FactorCollector)
        .map(CreditAggregator)
        .sink(CreditResultSink, output_file=output_file)
    )
    env.submit(autostop=True)
