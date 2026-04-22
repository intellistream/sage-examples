from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import BenchmarkWatchSink, BenchmarkSource, BenchmarkParser, BenchmarkDiffDetector, BenchmarkTrendTagger


def run_benchmark_watch_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment('benchmark_watch')
    (
        env.from_batch(BenchmarkSource, input_file=input_file)
        .map(BenchmarkParser)
        .map(BenchmarkDiffDetector)
        .map(BenchmarkTrendTagger)
        .sink(BenchmarkWatchSink, output_file=output_file)
    )
    env.submit(autostop=True)
