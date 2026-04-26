#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.media_archive_search import run_media_archive_search_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.media_archive_search: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run media archive search")
    parser.add_argument("--asset-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_media_archive_search_pipeline(args.asset_dir, args.output_dir)


if __name__ == "__main__":
    main()
