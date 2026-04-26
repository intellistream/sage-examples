from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    HighlightScorer,
    HighlightSink,
    HighlightTitleBuilder,
    PodcastSegmenter,
    PodcastTranscriptSource,
)


def run_podcast_highlight_pipeline(transcript_file: str, output_file: str) -> None:
    env = LocalEnvironment("podcast_highlight")
    (
        env.from_batch(PodcastTranscriptSource, transcript_file=transcript_file)
        .flatmap(PodcastSegmenter)
        .map(HighlightScorer)
        .map(HighlightTitleBuilder)
        .sink(HighlightSink, output_file=output_file)
    )
    env.submit(autostop=True)
