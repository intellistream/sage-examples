#!/usr/bin/env python3
"""Run the quality defect filter application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.quality_defect_filter import run_quality_defect_filter_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.quality_defect_filter: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run quality defect filtering")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_quality_defect_filter_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
