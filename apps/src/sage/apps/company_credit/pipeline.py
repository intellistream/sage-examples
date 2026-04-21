from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CompanyInfoFetcher,
    CompanySource,
    CreditReportSink,
    CreditScorer,
    RiskFactorExtractor,
)


def run_company_credit_pipeline(
    company_file: str, output_file: str, api_config: str | None = None
) -> None:
    env = LocalEnvironment("company_credit")
    (
        env.from_batch(CompanySource, company_file=company_file)
        .map(CompanyInfoFetcher, api_config=api_config)
        .map(RiskFactorExtractor)
        .map(CreditScorer)
        .sink(CreditReportSink, output_file=output_file)
    )
    env.submit(autostop=True)
