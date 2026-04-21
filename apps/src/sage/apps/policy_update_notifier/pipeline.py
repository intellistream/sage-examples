from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    PolicyDiffExtractor,
    PolicyImpactAnalyzer,
    PolicyNoticeSink,
    PolicyVersionSource,
)


def run_policy_update_notifier_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("policy_update_notifier")
    (
        env.from_batch(PolicyVersionSource, input_file=input_file)
        .map(PolicyDiffExtractor)
        .map(PolicyImpactAnalyzer)
        .sink(PolicyNoticeSink, output_file=output_file)
    )
    env.submit(autostop=True)
