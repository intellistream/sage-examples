#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.triage_structurer import run_triage_structurer_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.triage_structurer: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run triage structurer")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_triage_structurer_pipeline(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
