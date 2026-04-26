from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DrugFieldExtractor,
    DrugLeafletSink,
    DrugLeafletSource,
    DrugLeafletTextExtractor,
    DrugUnitNormalizer,
)


def run_drug_leaflet_extractor_pipeline(input_dir: str, output_file: str) -> None:
    env = LocalEnvironment("drug_leaflet_extractor")
    (
        env.from_batch(DrugLeafletSource, input_dir=input_dir)
        .map(DrugLeafletTextExtractor)
        .map(DrugFieldExtractor)
        .map(DrugUnitNormalizer)
        .sink(DrugLeafletSink, output_file=output_file)
    )
    env.submit(autostop=True)
