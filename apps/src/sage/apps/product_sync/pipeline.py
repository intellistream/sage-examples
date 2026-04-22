"""Product sync pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import DataValidator, FieldMapper, PlatformSink, ProductSource


def run_product_sync_pipeline(
    input_file: str,
    output_file: str,
    field_map: dict[str, str] | None = None,
) -> None:
    env = LocalEnvironment("product_sync")
    (
        env.from_batch(ProductSource, input_file=input_file)
        .map(FieldMapper, field_map=field_map)
        .map(DataValidator)
        .sink(PlatformSink, output_file=output_file)
    )
    env.submit(autostop=True)
