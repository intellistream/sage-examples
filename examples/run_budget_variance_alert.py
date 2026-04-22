#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.budget_variance_alert import run_budget_variance_alert_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.budget_variance_alert: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run budget variance alert pipeline")
    parser.add_argument("--plan-file", required=True)
    parser.add_argument("--actual-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_budget_variance_alert_pipeline(args.plan_file, args.actual_file, args.output_file)


if __name__ == "__main__":
    main()
