#!/usr/bin/env python3
"""Run the patent landscape mapper demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_SRC = PROJECT_ROOT / "apps" / "src"
if str(APPS_SRC) not in sys.path:
    sys.path.insert(0, str(APPS_SRC))

try:
    from sage.apps.patent_landscape_mapper import (
        print_patent_landscape_report,
        run_patent_landscape_mapper_pipeline,
    )
except ImportError as exc:
    print(f"Error importing sage.apps.patent_landscape_mapper: {exc}")
    print("\nPlease install sage-apps first:")
    print("  cd apps && python -m pip install -e .")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SAGE Patent Landscape Mapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/run_patent_landscape_mapper.py
  python examples/run_patent_landscape_mapper.py --clusters 5
  python examples/run_patent_landscape_mapper.py --focus-keywords "cold chain,biologics logistics"
  python examples/run_patent_landscape_mapper.py --json
        """,
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=4,
        help="Number of theme clusters to generate (default: 4).",
    )
    parser.add_argument(
        "--focus-keywords",
        type=str,
        default=None,
        help="Comma-separated strategic focus keywords.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full report as JSON.",
    )
    parser.add_argument(
        "--top-opportunities",
        type=int,
        default=3,
        help="How many whitespace opportunities to show in console mode.",
    )
    args = parser.parse_args()

    focus_keywords = None
    if args.focus_keywords:
        focus_keywords = [item.strip() for item in args.focus_keywords.split(",") if item.strip()]

    report = run_patent_landscape_mapper_pipeline(
        focus_keywords=focus_keywords,
        cluster_count=args.clusters,
    )

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    print_patent_landscape_report(report, top_opportunities=args.top_opportunities)


if __name__ == "__main__":
    main()
