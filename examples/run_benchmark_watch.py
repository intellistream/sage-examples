#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.benchmark_watch import run_benchmark_watch_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.benchmark_watch: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run benchmark watch")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_benchmark_watch_pipeline(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
