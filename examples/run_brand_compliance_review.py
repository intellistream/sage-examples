#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.brand_compliance_review import run_brand_compliance_review_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.brand_compliance_review: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run brand compliance review")
    parser.add_argument("--asset-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_brand_compliance_review_pipeline(args.asset_dir, args.output_file)


if __name__ == "__main__":
    main()
