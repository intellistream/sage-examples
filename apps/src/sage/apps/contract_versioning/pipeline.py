from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ContractTemplateSource,
    TemplateDiffAnalyzer,
    VersionParser,
    VersionRegistrySink,
)


def run_contract_versioning_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("contract_versioning")
    (
        env.from_batch(ContractTemplateSource, input_file=input_file)
        .map(VersionParser)
        .map(TemplateDiffAnalyzer)
        .sink(VersionRegistrySink, output_file=output_file)
    )
    env.submit(autostop=True)
