#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.campus_aid_gap_alert import run_campus_aid_gap_alert_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.campus_aid_gap_alert: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run campus aid gap alert pipeline")
    parser.add_argument("--application-file", required=True)
    parser.add_argument("--profile-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_campus_aid_gap_alert_pipeline(args.application_file, args.profile_file, args.output_file)


if __name__ == "__main__":
    main()
