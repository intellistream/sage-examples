from sage.apps.supply_chain_alert import SupplyChainAlertApplicationService


def test_run_demo_generates_multiple_alert_types(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")

    result = service.run_demo(reset=True)
    rule_ids = {item.rule_id for item in result.alerts}

    assert result.processed_event_count == 10
    assert result.alert_count >= 5
    assert "low_inventory" in rule_ids
    assert "shipment_delay" in rule_ids
    assert "supplier_risk_deterioration" in rule_ids
    assert result.dashboard.open_alert_count >= 5
    assert result.dashboard.high_risk_alert_count >= 3


def test_dashboard_summary_exposes_expected_metrics(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")

    service.run_demo(reset=True)
    dashboard = service.get_dashboard()

    assert dashboard.low_stock_sku_count >= 1
    assert dashboard.delayed_shipment_count == 1
    assert dashboard.overdue_order_count >= 1
    assert dashboard.average_delay_hours == 12.0
    assert "CHIP-A" in dashboard.top_shortage_skus
