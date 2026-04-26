from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import ContentCleaner, ContentSource, TagCandidateExtractor, TagSelector, TagSink


def run_content_tagger_pipeline(input_file: str, output_file: str, top_k: int = 8) -> None:
    env = LocalEnvironment("content_tagger")
    (
        env.from_batch(ContentSource, input_file=input_file)
        .map(ContentCleaner)
        .map(TagCandidateExtractor, top_k=top_k)
        .map(TagSelector)
        .sink(TagSink, output_file=output_file)
    )
    env.submit(autostop=True)
