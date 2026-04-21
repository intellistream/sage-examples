"""
Log Parser Pipeline

Main pipeline implementation using SAGE operators for enterprise log parsing.
"""

from __future__ import annotations

from sage.foundation import CustomLogger
from sage.runtime import LocalEnvironment

from .operators import (
    ConsoleSink,
    ErrorFilter,
    JsonSink,
    LogEnricher,
    LogParser,
    LogSource,
)


def run_log_parser_pipeline(
    log_file: str,
    output_file: str | None = None,
    error_levels: list[str] | None = None,
    verbose: bool = False,
    console_output: bool = False,
) -> None:
    """
    Run the log parser pipeline using SAGE framework.

    Args:
        log_file: Path to the log file to parse
        output_file: Path to output JSON file (optional, if None only console output)
        error_levels: List of error levels to filter (default: ERROR, CRITICAL, WARN)
        verbose: Enable verbose logging
        console_output: Also output to console (in addition to file)

    Example:
        >>> run_log_parser_pipeline(
        ...     log_file="app.log",
        ...     output_file="structured_logs.json",
        ...     error_levels=["ERROR", "CRITICAL"],
        ...     verbose=True
        ... )
    """
    logger = CustomLogger("LogParserPipeline")

    # Default parameters
    if error_levels is None:
        error_levels = ["ERROR", "CRITICAL", "WARN"]

    if verbose:
        logger.info(f"Starting log parser pipeline")
        logger.info(f"  Log file: {log_file}")
        logger.info(f"  Output file: {output_file}")
        logger.info(f"  Error levels: {error_levels}")

    # Create environment
    env = LocalEnvironment("log_parser")

    try:
        # Build pipeline
        pipeline = (
            env.from_batch(LogSource, log_file=log_file)
            .map(LogParser)
            .map(lambda log: log if log else None)
            .filter(lambda log: log is not None)
            .map(ErrorFilter, error_levels=error_levels)
            .filter(lambda log: log is not None)
            .map(LogEnricher)
        )

        # Add sinks
        if output_file:
            pipeline = pipeline.sink(JsonSink, output_file=output_file)

        if console_output:
            pipeline = pipeline.sink(ConsoleSink)

        # Submit and run
        env.submit(autostop=True)

        if verbose:
            logger.info("Log parser pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in log parser pipeline: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m sage.apps.log_parser <log_file> [output_file]")
        sys.exit(1)

    log_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    run_log_parser_pipeline(
        log_file=log_file, output_file=output_file, verbose=True, console_output=True
    )
