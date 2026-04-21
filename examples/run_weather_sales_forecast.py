#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.weather_sales_forecast import run_weather_sales_forecast_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.weather_sales_forecast: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run weather sales forecast")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_weather_sales_forecast_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
