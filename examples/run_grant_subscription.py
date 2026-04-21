#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.grant_subscription import run_grant_subscription_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.grant_subscription: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run grant subscription")
    parser.add_argument("--announcement-file", required=True)
    parser.add_argument("--profile-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_grant_subscription_pipeline(args.announcement_file, args.profile_file, args.output_file)


if __name__ == "__main__":
    main()
