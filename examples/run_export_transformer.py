#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.export_transformer import run_export_transformer_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.export_transformer: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run export transformer pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--output-format", default="json")
    args = parser.parse_args()
    run_export_transformer_pipeline(args.input_file, args.output, output_format=args.output_format)


if __name__ == "__main__":
    main()
