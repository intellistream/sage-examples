#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.factory_watch import run_factory_watch_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.factory_watch: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run factory watch")
    parser.add_argument("--sensor-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_factory_watch_pipeline(args.sensor_file, args.output_file)


if __name__ == "__main__":
    main()
