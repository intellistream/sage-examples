#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.experiment_review import run_experiment_review_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.experiment_review: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run experiment review")
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_experiment_review_pipeline(args.log_file, args.output_file)


if __name__ == "__main__":
    main()
