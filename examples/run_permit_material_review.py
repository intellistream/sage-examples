#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.permit_material_review import run_permit_material_review_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.permit_material_review: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run permit material review")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_permit_material_review_pipeline(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()
