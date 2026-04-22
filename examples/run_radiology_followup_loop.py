#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.radiology_followup_loop import run_radiology_followup_loop_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.radiology_followup_loop: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run radiology followup loop")
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--patient-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_radiology_followup_loop_pipeline(args.report_file, args.patient_file, args.output_file)


if __name__ == "__main__":
    main()
