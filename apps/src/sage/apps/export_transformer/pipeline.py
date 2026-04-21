from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import ExportFieldMapper, ExportQuerySource, ExportSink, FormatTransformer


def run_export_transformer_pipeline(
    input_file: str, output_file: str, output_format: str = "json"
) -> None:
    env = LocalEnvironment("export_transformer")
    (
        env.from_batch(ExportQuerySource, input_file=input_file)
        .map(ExportFieldMapper)
        .map(FormatTransformer, output_format=output_format)
        .sink(ExportSink, output_file=output_file)
    )
    env.submit(autostop=True)
