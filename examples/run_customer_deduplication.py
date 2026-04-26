#!/usr/bin/env python3
"""Run the customer deduplication application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.customer_deduplication import run_customer_deduplication_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.customer_deduplication: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run customer deduplication")
    parser.add_argument("--input-file", required=True, help="Input CSV file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--threshold", type=float, default=0.9, help="Duplicate threshold")
    args = parser.parse_args()
    run_customer_deduplication_pipeline(args.input_file, args.output, threshold=args.threshold)


if __name__ == "__main__":
    main()
