#!/usr/bin/env python3
"""Run the supply chain alert dashboard demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from sage.apps.supply_chain_alert import SupplyChainAlertApplicationService
except ImportError as exc:
    print(f"Error importing sage.apps.supply_chain_alert: {exc}")
    print("\nPlease install sage-apps first:")
    print("  cd apps && python -m pip install -e .")
    sys.exit(1)


def print_console_report(result, demo_summary: dict[str, int]) -> None:
    print("=" * 76)
    print("SAGE Supply Chain Alert Dashboard")
    print("=" * 76)
    print("运行配置")
    print("-" * 76)
    print(f"模拟仓库数量: {demo_summary['warehouse_count']}")
    print(f"供应商数量: {demo_summary['supplier_count']}")
    print(f"订单数量: {demo_summary['order_count']}")
    print(f"事件总数: {demo_summary['event_count']}")
    print()

    print("实时预警摘要")
    print("-" * 76)
    for alert in result.alerts:
        print(f"[{alert.risk_level.upper()}] {alert.title}")
        print(f"  规则: {alert.rule_id}")
        print(f"  摘要: {alert.summary}")
        print(f"  建议: {'; '.join(alert.recommended_actions)}")
        print()

    dashboard = result.dashboard
    print("最终看板")
    print("-" * 76)
    print(f"开放预警总数: {dashboard.open_alert_count}")
    print(f"高风险预警数: {dashboard.high_risk_alert_count}")
    print(f"即将缺货 SKU 数: {dashboard.low_stock_sku_count}")
    print(f"延迟运单数: {dashboard.delayed_shipment_count}")
    print(f"超期未发货订单数: {dashboard.overdue_order_count}")
    print(f"高风险供应商数: {dashboard.high_risk_supplier_count}")
    print(f"平均延迟小时数: {dashboard.average_delay_hours}")
    print(f"Top 风险供应商: {', '.join(item.supplier_id for item in dashboard.top_risk_suppliers)}")
    print(f"Top 缺货 SKU: {', '.join(dashboard.top_shortage_skus)}")


def print_explanation_report(explanation_result) -> None:
    print()
    print("自然语言风险解释")
    print("-" * 76)
    gateway_status = explanation_result.gateway_status
    if not gateway_status.reachable:
        print("SAGE gateway 当前不可用，未生成自然语言解释。")
        print(f"Health URL: {gateway_status.health_url}")
        if gateway_status.error:
            print(f"原因: {gateway_status.error}")
        return

    if gateway_status.error:
        print("SAGE gateway 已探测到，但解释生成失败。")
        print(f"原因: {gateway_status.error}")
        return

    print(f"Gateway Base URL: {gateway_status.base_url}")
    if gateway_status.model:
        print(f"使用模型: {gateway_status.model}")
    if explanation_result.dashboard_summary:
        print(f"管理摘要: {explanation_result.dashboard_summary}")
    for item in explanation_result.alert_explanations:
        print()
        print(f"[{item.risk_level.upper()}] {item.title}")
        print(f"  {item.explanation}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SAGE Supply Chain Alert Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/run_supply_chain_alert.py
  python examples/run_supply_chain_alert.py --json
    python examples/run_supply_chain_alert.py --explain
  python examples/run_supply_chain_alert.py --storage-path .sage/supply-chain-alert.json
        """,
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Optional JSON state path for persisting supply chain state.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output instead of a console summary.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Generate optional natural-language risk explanations via sage.serving.",
    )
    args = parser.parse_args()

    service = SupplyChainAlertApplicationService(storage_path=args.storage_path)
    result = service.run_demo(reset=True)
    explanation_result = service.explain_current_risks() if args.explain else None

    if args.json:
        payload = {"result": result.to_dict()}
        if explanation_result is not None:
            payload["explanations"] = explanation_result.to_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print_console_report(result, service.get_demo_summary())
    if explanation_result is not None:
        print_explanation_report(explanation_result)


if __name__ == "__main__":
    main()
