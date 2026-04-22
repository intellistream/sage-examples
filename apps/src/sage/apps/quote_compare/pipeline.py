from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import QuoteCompareSink, QuoteSource, QuoteNormalizer, QuoteConditionComparer, QuoteScorer


def run_quote_compare_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment('quote_compare')
    (
        env.from_batch(QuoteSource, input_dir=input_dir)
        .map(QuoteNormalizer)
        .map(QuoteConditionComparer)
        .map(QuoteScorer)
        .sink(QuoteCompareSink, output_file=output_file)
    )
    env.submit(autostop=True)
