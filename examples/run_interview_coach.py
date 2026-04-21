#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.interview_coach import run_interview_coach_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.interview_coach: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run interview coach")
    parser.add_argument("--answer-file", required=True)
    parser.add_argument("--rubric-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_interview_coach_pipeline(args.answer_file, args.rubric_file, args.output_file)


if __name__ == "__main__":
    main()
