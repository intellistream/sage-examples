"""
Data Cleaner Pipeline

Main pipeline implementation using SAGE operators for CSV/Excel data cleaning.
"""

from __future__ import annotations

from sage.foundation import CustomLogger
from sage.runtime import LocalEnvironment

from .operators import (
    AnomalyDetector,
    CleanedDataSink,
    CsvSource,
    DuplicateMarker,
    JsonSink,
    MissingValueFiller,
    TypeConverter,
)


def run_data_cleaner_pipeline(
    input_file: str,
    output_file: str,
    type_rules: dict[str, str] | None = None,
    fill_strategy: dict[str, str] | str | None = None,
    numeric_fields: list[str] | None = None,
    key_fields: list[str] | None = None,
    output_format: str = "csv",
    verbose: bool = False,
) -> None:
    """
    Run the data cleaner pipeline using SAGE framework.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV or JSON file
        type_rules: Dict mapping field names to types (int, float, bool, date)
        fill_strategy: Strategy for missing values ("drop", "forward", or dict)
        numeric_fields: List of numeric fields for anomaly detection
        key_fields: List of fields for duplicate detection
        output_format: Output format ("csv" or "json")
        verbose: Enable verbose logging

    Example:
        >>> run_data_cleaner_pipeline(
        ...     input_file="raw_data.csv",
        ...     output_file="cleaned_data.csv",
        ...     type_rules={"age": "int", "salary": "float"},
        ...     fill_strategy={"age": "0", "salary": "0"},
        ...     numeric_fields=["age", "salary"],
        ...     verbose=True
        ... )
    """
    logger = CustomLogger("DataCleanerPipeline")

    if verbose:
        logger.info(f"Starting data cleaner pipeline")
        logger.info(f"  Input file: {input_file}")
        logger.info(f"  Output file: {output_file}")
        logger.info(f"  Type rules: {type_rules}")
        logger.info(f"  Fill strategy: {fill_strategy}")

    # Create environment
    env = LocalEnvironment("data_cleaner")

    try:
        # Build pipeline
        pipeline = (
            env.from_batch(CsvSource, input_file=input_file)
            .map(TypeConverter, type_rules=type_rules or {})
            .map(MissingValueFiller, fill_strategy=fill_strategy or "drop")
            .filter(lambda row: row is not None)
        )

        # Add optional anomaly detection
        if numeric_fields:
            pipeline = pipeline.map(AnomalyDetector, numeric_fields=numeric_fields)

        # Add optional duplicate detection
        if key_fields:
            pipeline = pipeline.map(DuplicateMarker, key_fields=key_fields)

        # Add sink based on output format
        if output_format.lower() == "json":
            pipeline = pipeline.sink(JsonSink, output_file=output_file)
        else:
            pipeline = pipeline.sink(CleanedDataSink, output_file=output_file)

        # Submit and run
        env.submit(autostop=True)

        if verbose:
            logger.info("Data cleaner pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in data cleaner pipeline: {e}")
        raise
