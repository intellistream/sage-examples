#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.patent_competition_monitor import run_patent_competition_monitor_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.patent_competition_monitor: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run patent competition monitor")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_patent_competition_monitor_pipeline(args.input_file, args.output_dir)


if __name__ == "__main__":
    main()
