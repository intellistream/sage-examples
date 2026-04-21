#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.attendance_alert import run_attendance_alert_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.attendance_alert: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run attendance alerting")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--schedule-file")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_attendance_alert_pipeline(args.input_file, args.output, schedule_file=args.schedule_file)


if __name__ == "__main__":
    main()
