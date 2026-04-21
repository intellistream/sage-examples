from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import PolicyAnswerSink, PolicyDocSource, PolicyChunker, PolicyQuestionMatcher, PolicyAnswerComposer


def run_policy_search_helper_pipeline(doc_dir: str, question_file: str, output_file: str) -> None:
    env = LocalEnvironment('policy_search_helper')
    (
        env.from_batch(PolicyDocSource, doc_dir=doc_dir, question_file=question_file)
        .flatmap(PolicyChunker)
        .map(PolicyQuestionMatcher)
        .map(PolicyAnswerComposer)
        .sink(PolicyAnswerSink, output_file=output_file)
    )
    env.submit(autostop=True)
