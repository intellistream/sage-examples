#!/usr/bin/env python3
"""
Log Parser System Example

This script demonstrates the Log Parser application from sage-apps.
It reads log files in various formats, parses them, filters by error level,
and outputs structured JSON.

Requirements:
    pip install -e sage-apps
    # Or: pip install isage-apps

Usage:
    python examples/run_log_parser.py --log-file app.log --output structured.json
    python examples/run_log_parser.py --log-file app.log --console --verbose
    python examples/run_log_parser.py --help

Test Configuration:
    @test_category: apps
    @test_speed: fast
"""

import argparse
import sys

try:
    from sage.apps.log_parser import run_log_parser_pipeline
    from sage.foundation import CustomLogger
except ImportError as e:
    print(f"Error importing sage.apps.log_parser: {e}")
    print("\nPlease install sage-apps:")
    print("  cd sage-apps && pip install -e .")
    print("  Or: pip install isage-apps")
    sys.exit(1)


def main():
    """Run the log parser pipeline."""
    parser = argparse.ArgumentParser(
        description="SAGE Log Parser System - Parse and structure enterprise logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse log file and output to JSON
  python %(prog)s --log-file app.log --output structured.json

  # Parse and display to console
  python %(prog)s --log-file app.log --console --verbose

  # Custom error levels
  python %(prog)s \\
    --log-file app.log \\
    --output structured.json \\
    --error-levels ERROR,CRITICAL

  # Both file and console output
  python %(prog)s \\
    --log-file app.log \\
    --output structured.json \\
    --console
        """,
    )

    parser.add_argument(
        "--log-file",
        type=str,
        required=True,
        help="Path to the log file to parse",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (optional)",
    )

    parser.add_argument(
        "--error-levels",
        type=str,
        default="ERROR,CRITICAL,WARN",
        help="Comma-separated error levels to filter (default: ERROR,CRITICAL,WARN)",
    )

    parser.add_argument(
        "--console",
        action="store_true",
        help="Also output to console",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Parse error levels
    error_levels = [level.strip().upper() for level in args.error_levels.split(",")]

    if args.verbose:
        logger = CustomLogger("LogParserExample")
        logger.info("Starting Log Parser with:")
        logger.info(f"  Log file: {args.log_file}")
        logger.info(f"  Output file: {args.output}")
        logger.info(f"  Error levels: {error_levels}")

    try:
        run_log_parser_pipeline(
            log_file=args.log_file,
            output_file=args.output,
            error_levels=error_levels,
            verbose=args.verbose,
            console_output=args.console,
        )
    except KeyboardInterrupt:
        print("\n\nLog parser interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
