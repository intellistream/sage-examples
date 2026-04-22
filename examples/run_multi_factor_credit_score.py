#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.multi_factor_credit_score import run_multi_factor_credit_score_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.multi_factor_credit_score: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-factor credit scoring")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_multi_factor_credit_score_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
