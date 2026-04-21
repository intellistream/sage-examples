#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.assignment_feedback import run_assignment_feedback_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.assignment_feedback: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run assignment feedback")
    parser.add_argument("--draft-file", required=True)
    parser.add_argument("--rubric-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_assignment_feedback_pipeline(args.draft_file, args.rubric_file, args.output_file)


if __name__ == "__main__":
    main()
