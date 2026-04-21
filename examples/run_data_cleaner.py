#!/usr/bin/env python3
"""
Data Cleaner System Example

This script demonstrates the Data Cleaner application from sage-apps.
It reads CSV files, cleans data (type conversion, missing values, anomalies),
and outputs structured data in CSV or JSON format.

Requirements:
    pip install -e sage-apps
    # Or: pip install isage-apps

Usage:
    python examples/run_data_cleaner.py --input raw.csv --output cleaned.csv
    python examples/run_data_cleaner.py --input raw.csv --output cleaned.json --output-format json
    python examples/run_data_cleaner.py --help

Test Configuration:
    @test_category: apps
    @test_speed: fast
"""

import argparse
import sys

try:
    from sage.apps.data_cleaner import run_data_cleaner_pipeline
    from sage.foundation import CustomLogger
except ImportError as e:
    print(f"Error importing sage.apps.data_cleaner: {e}")
    print("\nPlease install sage-apps:")
    print("  cd sage-apps && pip install -e .")
    print("  Or: pip install isage-apps")
    sys.exit(1)


def parse_key_value_list(s: str) -> dict[str, str]:
    """Parse key:value,key:value format."""
    result = {}
    if not s:
        return result

    for pair in s.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def parse_list(s: str) -> list[str]:
    """Parse comma-separated list."""
    if not s:
        return []
    return [item.strip() for item in s.split(",")]


def main():
    """Run the data cleaner pipeline."""
    parser = argparse.ArgumentParser(
        description="SAGE Data Cleaner System - Clean and standardize CSV data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic cleaning
  python %(prog)s --input raw.csv --output cleaned.csv

  # Type conversion
  python %(prog)s \\
    --input raw.csv \\
    --output cleaned.csv \\
    --type-rules age:int,salary:float,active:bool,hire_date:date

  # With anomaly detection
  python %(prog)s \\
    --input raw.csv \\
    --output cleaned.csv \\
    --numeric-fields age,salary

  # JSON output with all features
  python %(prog)s \\
    --input raw.csv \\
    --output cleaned.json \\
    --output-format json \\
    --key-fields email,phone \\
    --numeric-fields age,salary

  # Custom missing value strategy
  python %(prog)s \\
    --input raw.csv \\
    --output cleaned.csv \\
    --fill-strategy drop
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV file",
    )

    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output file",
    )

    parser.add_argument(
        "--type-rules",
        type=str,
        default="",
        help="Type conversion rules (field:type,field:type). Types: int, float, bool, date",
    )

    parser.add_argument(
        "--numeric-fields",
        type=str,
        default="",
        help="Numeric fields for anomaly detection (comma-separated)",
    )

    parser.add_argument(
        "--key-fields",
        type=str,
        default="",
        help="Key fields for duplicate detection (comma-separated)",
    )

    parser.add_argument(
        "--fill-strategy",
        type=str,
        default="drop",
        help="Strategy for missing values: 'drop', 'forward', or 'field:value,field:value'",
    )

    parser.add_argument(
        "--output-format",
        type=str,
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Parse arguments
    type_rules = parse_key_value_list(args.type_rules)
    numeric_fields = parse_list(args.numeric_fields)
    key_fields = parse_list(args.key_fields)

    # Parse fill strategy
    if args.fill_strategy in ["drop", "forward"]:
        fill_strategy = args.fill_strategy
    else:
        fill_strategy = parse_key_value_list(args.fill_strategy)

    if args.verbose:
        logger = CustomLogger("DataCleanerExample")
        logger.info(f"Starting Data Cleaner with:")
        logger.info(f"  Input file: {args.input}")
        logger.info(f"  Output file: {args.output}")
        logger.info(f"  Type rules: {type_rules}")
        logger.info(f"  Numeric fields: {numeric_fields}")
        logger.info(f"  Key fields: {key_fields}")

    try:
        run_data_cleaner_pipeline(
            input_file=args.input,
            output_file=args.output,
            type_rules=type_rules or None,
            fill_strategy=fill_strategy,
            numeric_fields=numeric_fields or None,
            key_fields=key_fields or None,
            output_format=args.output_format,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\n\nData cleaner interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
