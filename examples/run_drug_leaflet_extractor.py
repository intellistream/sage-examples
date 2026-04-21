#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.drug_leaflet_extractor import run_drug_leaflet_extractor_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.drug_leaflet_extractor: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run drug leaflet extractor")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_drug_leaflet_extractor_pipeline(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()
