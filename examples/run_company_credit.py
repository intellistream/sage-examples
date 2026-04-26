#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.company_credit import run_company_credit_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.company_credit: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run company credit scoring")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--api-config")
    args = parser.parse_args()
    run_company_credit_pipeline(args.input_file, args.output, api_config=args.api_config)


if __name__ == "__main__":
    main()
