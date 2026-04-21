#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.compliance_doc_manager import run_compliance_doc_manager_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.compliance_doc_manager: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run compliance doc manager pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference-date")
    args = parser.parse_args()
    run_compliance_doc_manager_pipeline(
        args.input_file, args.output, reference_date=args.reference_date
    )


if __name__ == "__main__":
    main()
