from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import FeatureScorer, LeadSink, LeadSource, PriorityRanker


def run_lead_scoring_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("lead_scoring")
    (
        env.from_batch(LeadSource, input_file=input_file)
        .map(FeatureScorer)
        .map(PriorityRanker)
        .sink(LeadSink, output_file=output_file)
    )
    env.submit(autostop=True)
