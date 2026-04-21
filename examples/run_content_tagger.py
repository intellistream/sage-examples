#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.content_tagger import run_content_tagger_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.content_tagger: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run content tagger pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    args = parser.parse_args()
    run_content_tagger_pipeline(args.input_file, args.output, top_k=args.top_k)


if __name__ == "__main__":
    main()
