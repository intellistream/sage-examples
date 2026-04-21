#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.greenhouse_assistant import run_greenhouse_assistant_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.greenhouse_assistant: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run greenhouse assistant")
    parser.add_argument("--sensor-file", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_greenhouse_assistant_pipeline(args.sensor_file, args.task_file, args.output_file)


if __name__ == "__main__":
    main()
