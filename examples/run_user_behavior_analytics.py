#!/usr/bin/env python3
"""Run the user behavior analytics application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.user_behavior_analytics import run_user_behavior_analytics_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.user_behavior_analytics: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run user behavior analytics")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_user_behavior_analytics_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
