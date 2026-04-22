#!/usr/bin/env python3
"""Run the academic metadata application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.academic_metadata import run_academic_metadata_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.academic_metadata: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run academic metadata extraction")
    parser.add_argument("--input-path", required=True, help="Input file, CSV, or directory")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    run_academic_metadata_pipeline(args.input_path, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()
