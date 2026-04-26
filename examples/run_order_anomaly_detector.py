#!/usr/bin/env python3
"""Run the order anomaly detector application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.order_anomaly_detector import run_order_anomaly_detector_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.order_anomaly_detector: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run order anomaly detection")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_order_anomaly_detector_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
