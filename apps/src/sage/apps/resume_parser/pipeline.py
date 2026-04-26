"""
Resume Parser Pipeline

Main pipeline implementation using SAGE operators for resume parsing.
"""

from __future__ import annotations

from sage.foundation import CustomLogger
from sage.runtime import LocalEnvironment

from .operators import (
    DateNormalizer,
    InfoExtractor,
    ResumeSink,
    ResumeSource,
    TextExtractor,
)


def run_resume_parser_pipeline(
    resume_dir: str | None = None,
    resume_files: list[str] | None = None,
    output_file: str = "parsed_resumes.json",
    verbose: bool = False,
) -> None:
    """
    Run the resume parser pipeline using SAGE framework.

    Args:
        resume_dir: Directory containing resume files
        resume_files: List of resume file paths
        output_file: Path to output JSON file
        verbose: Enable verbose logging

    Example:
        >>> run_resume_parser_pipeline(
        ...     resume_dir="/path/to/resumes",
        ...     output_file="parsed_resumes.json",
        ...     verbose=True
        ... )
    """
    logger = CustomLogger("ResumeParserPipeline")

    if verbose:
        logger.info("Starting resume parser pipeline")
        logger.info(f"  Resume dir: {resume_dir}")
        logger.info(f"  Output file: {output_file}")

    # Create environment
    env = LocalEnvironment("resume_parser")

    try:
        # Build pipeline
        (
            env.from_batch(ResumeSource, resume_dir=resume_dir, resume_files=resume_files)
            .map(TextExtractor)
            .map(InfoExtractor)
            .map(DateNormalizer)
            .sink(ResumeSink, output_file=output_file)
        )

        # Submit and run
        env.submit(autostop=True)

        if verbose:
            logger.info("Resume parser pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in resume parser pipeline: {e}")
        raise
