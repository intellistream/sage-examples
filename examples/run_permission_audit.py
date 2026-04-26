#!/usr/bin/env python3
"""Run the permission audit application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.permission_audit import run_permission_audit_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.permission_audit: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run permission audit")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_permission_audit_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
