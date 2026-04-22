#!/usr/bin/env python3
"""Run the contract matcher application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.contract_matcher import run_contract_matcher_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.contract_matcher: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contract matcher")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--template-file")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    run_contract_matcher_pipeline(
        args.input_file, args.output, template_file=args.template_file, top_k=args.top_k
    )


if __name__ == "__main__":
    main()
