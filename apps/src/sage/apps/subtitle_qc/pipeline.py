from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import SubtitleQCSink, SubtitleSource, SubtitleBlockParser, SubtitleGlossaryChecker, SubtitleTimingChecker


def run_subtitle_qc_pipeline(subtitle_file: str, glossary_file: str, output_file: str) -> None:
    env = LocalEnvironment('subtitle_qc')
    (
        env.from_batch(SubtitleSource, subtitle_file=subtitle_file, glossary_file=glossary_file)
        .map(SubtitleBlockParser)
        .map(SubtitleGlossaryChecker)
        .map(SubtitleTimingChecker)
        .sink(SubtitleQCSink, output_file=output_file)
    )
    env.submit(autostop=True)
