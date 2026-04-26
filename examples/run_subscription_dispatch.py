#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.subscription_dispatch import run_subscription_dispatch_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.subscription_dispatch: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run subscription dispatch pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--subscription-file")
    args = parser.parse_args()
    run_subscription_dispatch_pipeline(
        args.input_file, args.output, subscription_file=args.subscription_file
    )


if __name__ == "__main__":
    main()
