#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.skill_gap_diagnosis import run_skill_gap_diagnosis_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.skill_gap_diagnosis: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run skill gap diagnosis")
    parser.add_argument("--record-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_skill_gap_diagnosis_pipeline(args.record_dir, args.output_file)


if __name__ == "__main__":
    main()
