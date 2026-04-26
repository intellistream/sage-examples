#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.return_reason_mining import run_return_reason_mining_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.return_reason_mining: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run return reason mining")
    parser.add_argument("--return-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_return_reason_mining_pipeline(args.return_file, args.output_file)


if __name__ == "__main__":
    main()
