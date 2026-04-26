from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CarbonCollectionSink,
    CarbonDataSource,
    CarbonFieldExtractor,
    CarbonLedgerBuilder,
    CarbonUnitNormalizer,
)


def run_carbon_collection_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment('carbon_collection')
    (
        env.from_batch(CarbonDataSource, input_dir=input_dir)
        .map(CarbonFieldExtractor)
        .map(CarbonUnitNormalizer)
        .map(CarbonLedgerBuilder)
        .sink(CarbonCollectionSink, output_file=output_file)
    )
    env.submit(autostop=True)
