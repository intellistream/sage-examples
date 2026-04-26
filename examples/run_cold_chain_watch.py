#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.cold_chain_watch import run_cold_chain_watch_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.cold_chain_watch: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cold chain watch")
    parser.add_argument("--record-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_cold_chain_watch_pipeline(args.record_file, args.output_file)


if __name__ == "__main__":
    main()
