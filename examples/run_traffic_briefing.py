#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.traffic_briefing import run_traffic_briefing_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.traffic_briefing: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run traffic briefing")
    parser.add_argument("--event-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_traffic_briefing_pipeline(args.event_file, args.output_file)


if __name__ == "__main__":
    main()
