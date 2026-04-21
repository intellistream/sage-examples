"""Content moderation pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ContentSource,
    ModerationSink,
    SensitiveFilter,
    TextExtractor,
    Tokenizer,
    ViolationScorer,
)


def run_content_moderation_pipeline(
    input_file: str, output_file: str, sensitive_words: list[str] | None = None
) -> None:
    env = LocalEnvironment("content_moderation")
    (
        env.from_batch(ContentSource, input_file=input_file)
        .map(TextExtractor)
        .flatmap(Tokenizer)
        .map(SensitiveFilter, sensitive_words=sensitive_words)
        .map(ViolationScorer)
        .sink(ModerationSink, output_file=output_file)
    )
    env.submit(autostop=True)
