#!/usr/bin/env python3
"""Run the student improvement app or one-shot demo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from sage.apps.student_improvement import StudentImprovementConsoleApp, run_demo_once
except ImportError as exc:
    print(f"Error importing sage.apps.student_improvement: {exc}")
    print("\nPlease install sage-apps first:")
    print("  cd apps && python -m pip install -e .")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SAGE Student Improvement App",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/run_student_improvement.py
  python examples/run_student_improvement.py --once
  python examples/run_student_improvement.py --json
  python examples/run_student_improvement.py --storage-path .sage/student-improvement.json
        """,
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Optional JSON state path for persisting curriculum and student state.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the two-exam demo once and exit instead of starting the interactive app.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output for the one-shot demo and exit.",
    )
    args = parser.parse_args()

    if args.json:
        run_demo_once(storage_path=args.storage_path, json_mode=True)
        return

    if args.once:
        run_demo_once(storage_path=args.storage_path, json_mode=False)
        return

    StudentImprovementConsoleApp(storage_path=args.storage_path).run()


if __name__ == "__main__":
    main()

