#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.project_risk_monitor import run_project_risk_monitor_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.project_risk_monitor: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run project risk monitor pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_project_risk_monitor_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
