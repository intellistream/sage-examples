#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.podcast_highlight import run_podcast_highlight_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.podcast_highlight: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run podcast highlight")
    parser.add_argument("--transcript-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_podcast_highlight_pipeline(args.transcript_file, args.output_file)


if __name__ == "__main__":
    main()
