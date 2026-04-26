#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.quote_compare import run_quote_compare_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.quote_compare: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run quote compare")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_quote_compare_pipeline(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()
