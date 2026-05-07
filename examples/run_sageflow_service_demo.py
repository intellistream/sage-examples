#!/usr/bin/env python3
"""Run the SageFlow-as-a-service snapshot handoff demo."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys

try:
    from sage.apps.sageflow_service_demo import (
        SageFlowServiceDemoApplication,
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


def print_console_report(result, demo_summary: dict[str, int], dataset: str) -> None:
    print("=" * 76)
    print("SAGE + SageFlow Service Demo")
    print("=" * 76)
    print("运行配置")
    print("-" * 76)
    print(f"数据集: {dataset}")
    print(f"输入事件数: {demo_summary['event_count']}")
    print(f"输入源数量: {demo_summary['source_count']}")
    print(f"高严重度事件数: {demo_summary['high_severity_events']}")
    print()

    print("SAGE 从 SageFlow 快照里提炼出的中间结论")
    print("-" * 76)
    for insight in result.insights:
        print(f"[{insight.severity.upper()}] {insight.title}")
        print(f"  类型: {insight.insight_type}")
        print(f"  摘要: {insight.summary}")
        if insight.related_cluster_id:
            print(f"  关联簇: {insight.related_cluster_id}")
        if insight.supporting_neighbor_ids:
            print(f"  近邻支撑: {', '.join(insight.supporting_neighbor_ids)}")
        print()

    snapshot = result.final_snapshot
    if snapshot is None:
        print("当前没有可用快照。")
        return

    print("最终窗口快照")
    print("-" * 76)
    print(f"窗口内事件数: {snapshot.window_size}")
    print(f"聚类数: {snapshot.cluster_count}")
    print(f"最新事件: {snapshot.latest_event_id}")
    print(f"来源分布: {json.dumps(snapshot.source_breakdown, ensure_ascii=False)}")
    print()
    for cluster in snapshot.hot_clusters:
        print(f"{cluster.cluster_id}: size={cluster.size}, avg_severity={cluster.average_severity}")
        print(f"  成员: {', '.join(cluster.member_ids)}")
        print(f"  标签: {', '.join(cluster.top_tags)}")
        print(f"  来源: {json.dumps(cluster.source_breakdown, ensure_ascii=False)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SAGE demo that treats SageFlow as a vector snapshot service.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output instead of a console summary.",
    )
    parser.add_argument(
        "--dataset",
        default="baseline",
        choices=available_demo_datasets(),
        help="Replay one of the repository-local vulnerability intelligence datasets.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=None,
        help="Override the adapter window size. Defaults to the dataset recommendation.",
    )
    args = parser.parse_args()

    dataset_info = describe_demo_dataset(args.dataset)
    service = SageFlowServiceDemoApplication(
        window_size=int(args.window_size or dataset_info["recommended_window_size"]),
    )

    if args.json:
        with _redirect_stdout_to_stderr():
            result = service.run_demo(reset=True, dataset=args.dataset)
    else:
        result = service.run_demo(reset=True, dataset=args.dataset)

    if args.json:
        print(json.dumps(service.to_payload(result), ensure_ascii=False, indent=2))
        return

    print_console_report(result, service.get_demo_summary(args.dataset), args.dataset)


if __name__ == "__main__":
    main()
