#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.paper_classifier import run_paper_classifier_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.paper_classifier: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paper classifier pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    run_paper_classifier_pipeline(args.input_file, args.output, top_k=args.top_k)


if __name__ == "__main__":
    main()
