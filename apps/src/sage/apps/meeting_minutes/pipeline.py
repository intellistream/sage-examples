from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ActionItemExtractor,
    AgendaSegmenter,
    MinutesFormatter,
    MinutesSink,
    TranscriptSource,
)


def run_meeting_minutes_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("meeting_minutes")
    (
        env.from_batch(TranscriptSource, input_file=input_file)
        .flatmap(AgendaSegmenter)
        .map(ActionItemExtractor)
        .map(MinutesFormatter)
        .sink(MinutesSink, output_file=output_file)
    )
    env.submit(autostop=True)
