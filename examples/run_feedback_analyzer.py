#!/usr/bin/env python3
"""
Feedback Analyzer System Example

This script demonstrates the Feedback Analyzer application from sage-apps.
It processes customer feedback, extracts keywords, and generates statistics.

Requirements:
    pip install -e sage-apps
    # Or: pip install isage-apps

Usage:
    python examples/run_feedback_analyzer.py --feedback-file feedback.txt --output keywords.json
    python examples/run_feedback_analyzer.py --feedback-file feedback.csv --delimiter "," --output keywords.json
    python examples/run_feedback_analyzer.py --help

Test Configuration:
    @test_category: apps
    @test_speed: fast
"""

import argparse
import sys

try:
    from sage.apps.feedback_analyzer import run_feedback_analyzer_pipeline
    from sage.foundation import CustomLogger
except ImportError as e:
    print(f"Error importing sage.apps.feedback_analyzer: {e}")
    print("\nPlease install sage-apps:")
    print("  cd sage-apps && pip install -e .")
    print("  Or: pip install isage-apps")
    sys.exit(1)


def main():
    """Run the feedback analyzer pipeline."""
    parser = argparse.ArgumentParser(
        description="SAGE Feedback Analyzer System - Extract keywords from customer feedback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic feedback analysis
  python %(prog)s --feedback-file feedback.txt --output keywords.json

  # CSV format feedback
  python %(prog)s \\
    --feedback-file feedback.csv \\
    --delimiter "," \\
    --output keywords.json

  # Custom top keywords count
  python %(prog)s \\
    --feedback-file feedback.txt \\
    --output keywords.json \\
    --top-n 100 \\
    --verbose
        """,
    )

    parser.add_argument(
        "--feedback-file",
        type=str,
        required=True,
        help="Path to feedback file (text or CSV)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="feedback_keywords.json",
        help="Output JSON file path (default: feedback_keywords.json)",
    )

    parser.add_argument(
        "--delimiter",
        type=str,
        default="\t",
        help="CSV delimiter (default: tab)",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="Number of top keywords to include (default: 50)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logger = CustomLogger("FeedbackAnalyzerExample")
        logger.info("Starting Feedback Analyzer with:")
        logger.info(f"  Feedback file: {args.feedback_file}")
        logger.info(f"  Output file: {args.output}")
        logger.info(f"  Top keywords: {args.top_n}")

    try:
        run_feedback_analyzer_pipeline(
            feedback_file=args.feedback_file,
            output_file=args.output,
            top_n=args.top_n,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\n\nFeedback analyzer interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
