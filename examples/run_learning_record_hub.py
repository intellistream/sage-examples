#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.learning_record_hub import run_learning_record_hub_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.learning_record_hub: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run learning record hub pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_learning_record_hub_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
