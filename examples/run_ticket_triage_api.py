#!/usr/bin/env python3
"""Run the customer support ticket triage FastAPI service."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import uvicorn
    from sage.apps.ticket_triage import TicketTriageApplicationService, create_fastapi_app
except ImportError as exc:
    print(f"Error importing ticket triage API dependencies: {exc}")
    print("\nPlease install sage-apps dependencies in your active environment.")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the SAGE Ticket Triage FastAPI service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/run_ticket_triage_api.py
  python examples/run_ticket_triage_api.py --host 0.0.0.0 --port 8020
  python examples/run_ticket_triage_api.py --storage-path .sage/ticket-triage-state.json
        """,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the API server.")
    parser.add_argument("--port", type=int, default=8010, help="Port to bind the API server.")
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Optional JSON state path for persisting ticket triage state.",
    )
    args = parser.parse_args()

    service = TicketTriageApplicationService(storage_path=args.storage_path)
    app = create_fastapi_app(service)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()