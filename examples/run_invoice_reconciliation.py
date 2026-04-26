#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.invoice_reconciliation import run_invoice_reconciliation_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.invoice_reconciliation: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run invoice reconciliation pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--order-file")
    parser.add_argument("--tolerance", type=float, default=1.0)
    args = parser.parse_args()
    run_invoice_reconciliation_pipeline(
        args.input_file, args.output, order_file=args.order_file, tolerance=args.tolerance
    )


if __name__ == "__main__":
    main()
