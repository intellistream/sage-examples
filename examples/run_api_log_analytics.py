#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.api_log_analytics import run_api_log_analytics_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.api_log_analytics: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run API log analytics pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_api_log_analytics_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
