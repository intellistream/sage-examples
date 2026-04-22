#!/usr/bin/env python3
"""Run the inventory alert application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.inventory_alert import run_inventory_alert_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.inventory_alert: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run inventory alerting")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_inventory_alert_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
