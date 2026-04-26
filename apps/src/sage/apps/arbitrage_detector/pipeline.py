from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ArbitrageMatcher,
    ArbitrageSink,
    ConversionCalculator,
    ExchangeRateFetcher,
    OrderSource,
)


def run_arbitrage_detector_pipeline(
    input_file: str, output_file: str, static_rates: dict[str, float] | None = None
) -> None:
    env = LocalEnvironment("arbitrage_detector")
    (
        env.from_batch(OrderSource, input_file=input_file)
        .map(ExchangeRateFetcher, static_rates=static_rates)
        .map(ConversionCalculator)
        .map(ArbitrageMatcher)
        .sink(ArbitrageSink, output_file=output_file)
    )
    env.submit(autostop=True)
