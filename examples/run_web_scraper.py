#!/usr/bin/env python3
"""Run the web scraper application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.web_scraper import run_web_scraper_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.web_scraper: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SAGE web scraper")
    parser.add_argument("--url-file", required=True, help="Text file with one URL per line")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    run_web_scraper_pipeline(args.url_file, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()
