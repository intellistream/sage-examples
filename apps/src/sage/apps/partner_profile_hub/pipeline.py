from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    PartnerDeduplicator,
    PartnerFieldMapper,
    PartnerProfileBuilder,
    PartnerSink,
    PartnerSource,
)


def run_partner_profile_hub_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("partner_profile_hub")
    (
        env.from_batch(PartnerSource, input_file=input_file)
        .map(PartnerFieldMapper)
        .map(PartnerDeduplicator)
        .map(PartnerProfileBuilder)
        .sink(PartnerSink, output_file=output_file)
    )
    env.submit(autostop=True)
