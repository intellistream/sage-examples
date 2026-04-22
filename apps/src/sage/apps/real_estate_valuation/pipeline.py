from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    NearbyListingFetcher,
    PropertySource,
    ValuationCalculator,
    ValuationFeatureBuilder,
    ValuationSink,
)


def run_real_estate_valuation_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("real_estate_valuation")
    (
        env.from_batch(PropertySource, input_file=input_file)
        .map(NearbyListingFetcher)
        .map(ValuationFeatureBuilder)
        .map(ValuationCalculator)
        .sink(ValuationSink, output_file=output_file)
    )
    env.submit(autostop=True)
