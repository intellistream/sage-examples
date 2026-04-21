"""Contract matcher pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import KeywordExtractor, MatchSink, RequirementSource, TemplateMatcher


def run_contract_matcher_pipeline(
    input_file: str,
    output_file: str,
    template_file: str | None = None,
    top_k: int = 3,
) -> None:
    env = LocalEnvironment("contract_matcher")
    (
        env.from_batch(RequirementSource, input_file=input_file)
        .map(KeywordExtractor)
        .map(TemplateMatcher, template_file=template_file, top_k=top_k)
        .sink(MatchSink, output_file=output_file)
    )
    env.submit(autostop=True)
