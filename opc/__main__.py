"""CLI entry point for running the SAGE OPC web console."""

from __future__ import annotations

import argparse
import sys

import uvicorn

from .server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SAGE OPC web console")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the OPC control plane.")
    parser.add_argument("--port", type=int, default=18400, help="Port for the OPC control plane.")
    parser.add_argument(
        "--root-dir",
        default=None,
        help="Repository root for sage-examples. Defaults to the current repo root.",
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python interpreter used to spawn child apps.",
    )
    parser.add_argument(
        "--port-range-start",
        type=int,
        default=18000,
        help="First port available for managed apps.",
    )
    parser.add_argument(
        "--port-range-end",
        type=int,
        default=18100,
        help="Last port available for managed apps.",
    )
    args = parser.parse_args()

    app = create_app(
        root_dir=args.root_dir,
        python_executable=args.python_executable,
        port_range_start=args.port_range_start,
        port_range_end=args.port_range_end,
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()