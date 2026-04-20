#!/usr/bin/env python3
"""Run the supply chain alert FastAPI service."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import uvicorn
    from sage.apps.supply_chain_alert import (
        SupplyChainAlertApplicationService,
        create_fastapi_app,
    )
except ImportError as exc:
    print(f"Error importing supply chain alert API dependencies: {exc}")
    print("\nPlease install sage-apps dependencies in your active environment.")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the SAGE Supply Chain Alert FastAPI service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/run_supply_chain_alert_api.py
  python examples/run_supply_chain_alert_api.py --host 0.0.0.0 --port 8010
  python examples/run_supply_chain_alert_api.py --storage-path .sage/supply-chain-alert.json
        """,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the API server.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the API server.")
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Optional JSON state path for persisting supply chain state.",
    )
    args = parser.parse_args()

    service = SupplyChainAlertApplicationService(storage_path=args.storage_path)
    app = create_fastapi_app(service)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()