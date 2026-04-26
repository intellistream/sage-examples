from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    MunicipalAnswerFormatter,
    MunicipalChunker,
    MunicipalDocSource,
    MunicipalQuestionMatcher,
    MunicipalSearchSink,
)


def run_municipal_search_pipeline(doc_dir: str, question_file: str, output_file: str) -> None:
    env = LocalEnvironment("municipal_search")
    (
        env.from_batch(MunicipalDocSource, doc_dir=doc_dir, question_file=question_file)
        .flatmap(MunicipalChunker)
        .map(MunicipalQuestionMatcher)
        .map(MunicipalAnswerFormatter)
        .sink(MunicipalSearchSink, output_file=output_file)
    )
    env.submit(autostop=True)
