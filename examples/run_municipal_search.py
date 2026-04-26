#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.municipal_search import run_municipal_search_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.municipal_search: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run municipal search")
    parser.add_argument("--doc-dir", required=True)
    parser.add_argument("--question-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_municipal_search_pipeline(args.doc_dir, args.question_file, args.output_file)


if __name__ == "__main__":
    main()
