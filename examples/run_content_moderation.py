#!/usr/bin/env python3
"""Run the content moderation application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.content_moderation import run_content_moderation_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.content_moderation: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run content moderation")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_content_moderation_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
