"""Document classifier pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import Classifier, DocSink, DocSource, FeatureExtractor, TextExtractor, Tokenizer


def run_doc_classifier_pipeline(
    input_file: str,
    output_file: str,
    label_rules: dict[str, list[str]] | None = None,
) -> None:
    env = LocalEnvironment("doc_classifier")
    (
        env.from_batch(DocSource, input_file=input_file)
        .map(TextExtractor)
        .flatmap(Tokenizer)
        .map(FeatureExtractor)
        .map(Classifier, label_rules=label_rules)
        .sink(DocSink, output_file=output_file)
    )
    env.submit(autostop=True)
