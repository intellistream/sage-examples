#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.meeting_minutes import run_meeting_minutes_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.meeting_minutes: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run meeting minutes pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_meeting_minutes_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
