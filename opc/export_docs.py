"""CLI helpers for exporting OPC markdown reports."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .runtime import ProcessRuntimeAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Export SAGE OPC markdown reports")
    parser.add_argument("report", choices=["inventory", "compatibility"])
    parser.add_argument(
        "--root-dir",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root for sage-examples.",
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python interpreter value to embed in generated previews when needed.",
    )
    args = parser.parse_args()

    runtime = ProcessRuntimeAdapter(
        Path(args.root_dir),
        python_executable=args.python_executable,
    )
    if args.report == "inventory":
        sys.stdout.write(runtime.export_inventory_markdown())
        return
    sys.stdout.write(runtime.export_compatibility_markdown())


if __name__ == "__main__":
    main()