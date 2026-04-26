#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.backup_sync import run_backup_sync_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.backup_sync: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run backup sync pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_backup_sync_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
