#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.urban_repair_scheduler import run_urban_repair_scheduler_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.urban_repair_scheduler: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run urban repair scheduler")
    parser.add_argument("--ticket-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_urban_repair_scheduler_pipeline(args.ticket_file, args.output_file)


if __name__ == "__main__":
    main()
