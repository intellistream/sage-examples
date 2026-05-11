#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPS_SRC = REPO_ROOT / "apps" / "src"
CORE_SRC = REPO_ROOT.parent / "SAGE" / "src"

if APPS_SRC.exists() and str(APPS_SRC) not in sys.path:
    sys.path.insert(0, str(APPS_SRC))

if CORE_SRC.exists() and str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

try:
    from sage.apps.traffic_briefing import run_traffic_briefing_pipeline  # pyright: ignore[reportMissingImports]
except ImportError as exc:
    print(f"Error importing sage.apps.traffic_briefing: {exc}")
    print("\nPlease install sage-apps first, or run from the monorepo with local sources available.")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run traffic briefing")
    parser.add_argument("--event-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_traffic_briefing_pipeline(args.event_file, args.output_file)


if __name__ == "__main__":
    main()
