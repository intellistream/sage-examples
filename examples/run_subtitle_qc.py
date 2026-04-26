#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.subtitle_qc import run_subtitle_qc_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.subtitle_qc: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run subtitle qc")
    parser.add_argument("--subtitle-file", required=True)
    parser.add_argument("--glossary-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_subtitle_qc_pipeline(args.subtitle_file, args.glossary_file, args.output_file)


if __name__ == "__main__":
    main()
