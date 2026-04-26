"""
Feedback Analyzer Pipeline

Main pipeline implementation using SAGE operators for customer feedback analysis.
"""

from __future__ import annotations

from sage.foundation import CustomLogger
from sage.runtime import LocalEnvironment

from .operators import (
    FeedbackSource,
    KeywordExtractor,
    KeywordScorer,
    SimpleTokenizer,
    StatisticsSink,
    TextCleaner,
)


def run_feedback_analyzer_pipeline(
    feedback_file: str,
    output_file: str = "feedback_keywords.json",
    top_n: int = 50,
    verbose: bool = False,
) -> None:
    """
    Run the feedback analyzer pipeline using SAGE framework.

    Args:
        feedback_file: Path to feedback file
        output_file: Path to output JSON statistics file
        top_n: Number of top keywords to include in output
        verbose: Enable verbose logging

    Example:
        >>> run_feedback_analyzer_pipeline(
        ...     feedback_file="feedback.txt",
        ...     output_file="keywords.json",
        ...     top_n=50,
        ...     verbose=True
        ... )
    """
    logger = CustomLogger("FeedbackAnalyzerPipeline")

    if verbose:
        logger.info("Starting feedback analyzer pipeline")
        logger.info(f"  Feedback file: {feedback_file}")
        logger.info(f"  Output file: {output_file}")
        logger.info(f"  Top keywords: {top_n}")

    # Create environment
    env = LocalEnvironment("feedback_analyzer")

    try:
        # Build pipeline
        (
            env.from_batch(FeedbackSource, feedback_file=feedback_file)
            .map(TextCleaner)
            .flatmap(SimpleTokenizer, min_length=2)
            .map(KeywordScorer)
            .filter(lambda token: token is not None)
            .map(KeywordExtractor, top_n=top_n)
            .filter(lambda token: token is not None)
            .sink(StatisticsSink, output_file=output_file)
        )

        # Submit and run
        env.submit(autostop=True)

        if verbose:
            logger.info("Feedback analyzer pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in feedback analyzer pipeline: {e}")
        raise
