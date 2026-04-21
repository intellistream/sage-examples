#!/usr/bin/env python3
"""Run the news aggregator application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.news_aggregator import run_news_aggregator_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.news_aggregator: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run news aggregation")
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_news_aggregator_pipeline(args.source_file, args.output)


if __name__ == "__main__":
    main()
