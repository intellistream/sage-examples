#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.lab_turnaround_alert import run_lab_turnaround_alert_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.lab_turnaround_alert: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lab turnaround alert pipeline")
    parser.add_argument("--record-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_lab_turnaround_alert_pipeline(args.record_file, args.output_file)


if __name__ == "__main__":
    main()
