#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.data_center_watch import run_data_center_watch_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.data_center_watch: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run data center watch")
    parser.add_argument("--metric-file", required=True)
    parser.add_argument("--alert-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_data_center_watch_pipeline(args.metric_file, args.alert_file, args.output_file)


if __name__ == "__main__":
    main()
