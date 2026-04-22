#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.solar_alerting import run_solar_alerting_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.solar_alerting: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run solar alerting")
    parser.add_argument("--sensor-file", required=True)
    parser.add_argument("--weather-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_solar_alerting_pipeline(args.sensor_file, args.weather_file, args.output_file)


if __name__ == "__main__":
    main()
