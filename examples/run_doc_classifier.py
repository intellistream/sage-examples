#!/usr/bin/env python3
"""Run the document classifier application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.doc_classifier import run_doc_classifier_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.doc_classifier: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run document classification")
    parser.add_argument("--input-file", required=True, help="Input text, CSV, or JSON file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()
    run_doc_classifier_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
