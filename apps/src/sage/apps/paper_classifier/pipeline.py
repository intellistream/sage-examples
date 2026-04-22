from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    PaperClassificationSink,
    PaperKeywordExtractor,
    PaperSource,
    PaperTopicClassifier,
)


def run_paper_classifier_pipeline(input_file: str, output_file: str, top_k: int = 5) -> None:
    env = LocalEnvironment("paper_classifier")
    (
        env.from_batch(PaperSource, input_file=input_file)
        .map(PaperKeywordExtractor, top_k=top_k)
        .map(PaperTopicClassifier)
        .sink(PaperClassificationSink, output_file=output_file)
    )
    env.submit(autostop=True)
