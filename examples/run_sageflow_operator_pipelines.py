#!/usr/bin/env python3
"""Run the multi-operator SageFlow service demos used by the ICPP narrative."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path


def _bootstrap_workspace_apps() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    apps_src = Path(__file__).resolve().parents[1] / "apps" / "src"
    sage_src = workspace_root / "SAGE" / "src"
    sageflow_root = workspace_root / "sageFlow"

    for path in (apps_src, sage_src, sageflow_root):
        path_str = str(path)
        if path.is_dir() and path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_workspace_apps()

try:
    from sage.apps.sageflow_service_demo import (
        SageFlowSecurityEscalationApplication,
        SageFlowServiceDemoApplication,
        SageFlowTriageRoutingApplication,
        available_demo_datasets,
        describe_demo_dataset,
    )
except ImportError as exc:
    print(f"Error importing sage.apps.sageflow_service_demo: {exc}")
    print("\nPlease install sage-apps first:")
    print("  cd apps && python -m pip install -e .")
    sys.exit(1)


@contextlib.contextmanager
def _redirect_stdout_to_stderr():
    saved_stdout = os.dup(1)
    os.dup2(2, 1)
    try:
        yield
    finally:
        os.dup2(saved_stdout, 1)
        os.close(saved_stdout)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the join/snapshot, filter+Top-K, and filter+join SageFlow demos.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    parser.add_argument(
        "--dataset",
        default="medium",
        choices=available_demo_datasets(),
        help="Choose which repo-local real dataset profile to replay.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=None,
        help="Override the adapter window size. Defaults to the dataset recommendation.",
    )
    args = parser.parse_args()

    dataset_info = describe_demo_dataset(args.dataset)
    window_size = int(args.window_size or dataset_info["recommended_window_size"])

    snapshot_app = SageFlowServiceDemoApplication(window_size=window_size)
    triage_app = SageFlowTriageRoutingApplication(window_size=window_size)
    security_app = SageFlowSecurityEscalationApplication(window_size=window_size)

    def run_payload() -> dict[str, object]:
        payload = {
            "snapshot_pipeline": snapshot_app.to_payload(
                snapshot_app.run_demo(reset=True, dataset=args.dataset)
            ),
            "triage_pipeline": triage_app.to_payload(triage_app.run_demo(reset=True, dataset=args.dataset)),
            "security_pipeline": security_app.to_payload(
                security_app.run_demo(reset=True, dataset=args.dataset)
            ),
        }
        snapshot_app.workflow.adapter.close()
        triage_app.adapter.close()
        security_app.adapter.close()
        return payload

    if args.json:
        with _redirect_stdout_to_stderr():
            payload = run_payload()
    else:
        payload = run_payload()

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print("SAGE + SageFlow Operator Mix Demo")
    print("=" * 76)
    print(f"dataset: {dataset_info['dataset']} ({dataset_info['event_count']} events)")
    print("1. Join-backed snapshot pipeline")
    print(f"   insights: {payload['snapshot_pipeline']['insight_count']}")
    print(f"   clusters: {payload['snapshot_pipeline']['final_snapshot']['cluster_count']}")
    print()
    print("2. Filter + window + Top-K triage pipeline")
    for item in payload["triage_pipeline"][-3:]:
        print(f"   {item['event_id']} -> {item['route']} ({item['priority']})")
    print()
    print("3. Filter + join security escalation pipeline")
    for item in payload["security_pipeline"][-3:]:
        print(f"   {item['event_id']} -> {item['action']} [{item['severity']}]")


if __name__ == "__main__":
    main()
