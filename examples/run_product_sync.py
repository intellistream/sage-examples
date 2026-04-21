#!/usr/bin/env python3
"""Run the product sync application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.product_sync import run_product_sync_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.product_sync: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run product synchronization")
    parser.add_argument("--input-file", required=True, help="Input CSV or JSON file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()
    run_product_sync_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
