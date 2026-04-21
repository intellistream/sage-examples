#!/usr/bin/env python3
"""Run the ticket router application."""

from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.ticket_router import run_ticket_router_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.ticket_router: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ticket routing")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--agents", default="agent_a,agent_b,agent_c")
    args = parser.parse_args()
    agents = [value.strip() for value in args.agents.split(",") if value.strip()]
    run_ticket_router_pipeline(args.input_file, args.output, agents=agents)


if __name__ == "__main__":
    main()
