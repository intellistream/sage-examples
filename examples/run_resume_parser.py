#!/usr/bin/env python3
"""
Resume Parser System Example

This script demonstrates the Resume Parser application from sage-apps.
It reads resume files, extracts structured information, and outputs JSON.

Requirements:
    pip install -e sage-apps
    # Or: pip install isage-apps

Usage:
    python examples/run_resume_parser.py --resume-dir ./resumes --output parsed.json
    python examples/run_resume_parser.py --resume-files resume1.txt resume2.txt --output parsed.json
    python examples/run_resume_parser.py --help

Test Configuration:
    @test_category: apps
    @test_speed: fast
"""

import argparse
import sys

try:
    from sage.apps.resume_parser import run_resume_parser_pipeline
    from sage.foundation import CustomLogger
except ImportError as e:
    print(f"Error importing sage.apps.resume_parser: {e}")
    print("\nPlease install sage-apps:")
    print("  cd sage-apps && pip install -e .")
    print("  Or: pip install isage-apps")
    sys.exit(1)


def main():
    """Run the resume parser pipeline."""
    parser = argparse.ArgumentParser(
        description="SAGE Resume Parser System - Parse and structure resume data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse resumes from directory
  python %(prog)s --resume-dir ./resumes --output parsed.json

  # Parse specific files
  python %(prog)s \\
    --resume-files resume1.txt resume2.txt resume3.txt \\
    --output parsed.json

  # With verbose logging
  python %(prog)s \\
    --resume-dir ./resumes \\
    --output parsed.json \\
    --verbose
        """,
    )

    parser.add_argument(
        "--resume-dir",
        type=str,
        default=None,
        help="Directory containing resume files",
    )

    parser.add_argument(
        "--resume-files",
        type=str,
        nargs="*",
        default=None,
        help="List of resume file paths",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="parsed_resumes.json",
        help="Output JSON file path (default: parsed_resumes.json)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if not args.resume_dir and not args.resume_files:
        parser.print_help()
        print("\nError: Please specify either --resume-dir or --resume-files")
        sys.exit(1)

    if args.verbose:
        logger = CustomLogger("ResumeParserExample")
        logger.info("Starting Resume Parser with:")
        logger.info(f"  Resume dir: {args.resume_dir}")
        logger.info(f"  Resume files: {args.resume_files}")
        logger.info(f"  Output file: {args.output}")

    try:
        run_resume_parser_pipeline(
            resume_dir=args.resume_dir,
            resume_files=args.resume_files,
            output_file=args.output,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\n\nResume parser interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
