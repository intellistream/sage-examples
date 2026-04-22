#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.lesson_scheduler import run_lesson_scheduler_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.lesson_scheduler: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lesson scheduler")
    parser.add_argument("--plan-file", required=True)
    parser.add_argument("--resource-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_lesson_scheduler_pipeline(args.plan_file, args.resource_file, args.output_file)


if __name__ == "__main__":
    main()
