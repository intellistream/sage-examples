#!/usr/bin/env python3
"""Run the contract risk application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.contract_risk import run_contract_risk_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.contract_risk: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contract risk analysis")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_contract_risk_pipeline(args.input_path, args.output)


if __name__ == "__main__":
    main()
