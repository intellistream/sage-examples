#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.warehouse_slot_optimizer import run_warehouse_slot_optimizer_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.warehouse_slot_optimizer: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run warehouse slot optimization")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_warehouse_slot_optimizer_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
