#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.vendor_evaluation_standardizer import run_vendor_evaluation_standardizer_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.vendor_evaluation_standardizer: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vendor evaluation standardizer pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_vendor_evaluation_standardizer_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
