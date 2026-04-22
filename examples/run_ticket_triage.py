#!/usr/bin/env python3
"""Run the customer support ticket triage demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from sage.apps.ticket_triage import TicketTriageApplicationService
except ImportError as exc:
    print(f"Error importing sage.apps.ticket_triage: {exc}")
    print("\nPlease install sage-apps first:")
    print("  cd apps && python -m pip install -e .")
    sys.exit(1)


def print_console_report(result, demo_summary: dict[str, int]) -> None:
    print("=" * 76)
    print("SAGE Customer Support Ticket Triage")
    print("=" * 76)
    print("运行配置")
    print("-" * 76)
    print(f"模拟工单数: {demo_summary['ticket_count']}")
    print(f"渠道数: {demo_summary['channel_count']}")
    print(f"客户数: {demo_summary['customer_count']}")
    print(f"FAQ 条目数: {demo_summary['knowledge_article_count']}")
    print(f"历史案例数: {demo_summary['historical_case_count']}")
    print()

    print("分诊结果")
    print("-" * 76)
    for item in result.triage_results:
        print(f"[{item.priority.upper()}] {item.ticket_id} -> {item.assigned_team}")
        print(f"  意图: {item.intent}")
        print(f"  动作: {item.recommended_action}")
        if item.reply_draft:
            print(f"  自动回复: {item.reply_draft}")
        print(f"  解释: {'; '.join(item.reason_trace[:3])}")
        print()

    print("队列摘要")
    print("-" * 76)
    for queue in result.queue_summaries:
        print(
            f"{queue.team_name}: open={queue.open_ticket_count}, "
            f"high={queue.high_priority_count}, auto_reply={queue.auto_reply_candidate_count}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SAGE Customer Support Ticket Triage",
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Optional JSON state path for persisting ticket state.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output instead of a console summary.",
    )
    args = parser.parse_args()

    service = TicketTriageApplicationService(storage_path=args.storage_path)
    result = service.run_demo(reset=True)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    print_console_report(result, service.get_demo_summary())


if __name__ == "__main__":
    main()
