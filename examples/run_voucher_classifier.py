#!/usr/bin/env python3
"""Run the voucher classifier application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.voucher_classifier import run_voucher_classifier_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.voucher_classifier: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run voucher classification")
    parser.add_argument("--input-file", required=True, help="Input CSV or text file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()
    run_voucher_classifier_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
