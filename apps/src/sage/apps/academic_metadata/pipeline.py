"""Academic metadata pipeline."""

from __future__ import annotations

from sage.foundation import CustomLogger
from sage.runtime import LocalEnvironment

from .operators import AuthorNormalizer, MetadataExtractor, MetadataSink, PdfSource, TextExtractor


def run_academic_metadata_pipeline(
    input_path: str,
    output_file: str,
    verbose: bool = False,
) -> None:
    logger = CustomLogger("AcademicMetadataPipeline")
    if verbose:
        logger.info(f"Starting academic metadata extraction: {input_path}")

    env = LocalEnvironment("academic_metadata")
    (
        env.from_batch(PdfSource, input_path=input_path)
        .map(TextExtractor)
        .map(MetadataExtractor)
        .map(AuthorNormalizer)
        .sink(MetadataSink, output_file=output_file)
    )
    env.submit(autostop=True)
