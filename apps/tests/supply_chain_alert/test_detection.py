from sage.apps.supply_chain_alert import SupplyChainAlertApplicationService
from sage.apps.supply_chain_alert.models import (
    InventoryEvent,
    PurchaseOrderEvent,
    ShipmentEvent,
    SupplierPerformanceEvent,
)


def test_low_inventory_triggers_reallocation_recommendation(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")

    result = service.ingest_events(
        [
            InventoryEvent(
                event_id="inventory:bj:chip-a:1",
                sku="CHIP-A",
                warehouse="WH-BJ",
                current_stock=80,
                safety_stock=20,
                updated_at="2026-01-15T09:00:00",
            ),
            InventoryEvent(
                event_id="inventory:sh:chip-a:1",
                sku="CHIP-A",
                warehouse="WH-SH",
                current_stock=10,
                safety_stock=30,
                updated_at="2026-01-15T09:01:00",
            ),
        ]
    )

    low_inventory_alert = next(item for item in result.alerts if item.rule_id == "low_inventory")

    assert low_inventory_alert.risk_level in {"medium", "high"}
    assert any("调拨" in action for action in low_inventory_alert.recommended_actions)


def test_delayed_shipment_is_assessed_as_high_risk(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")

    result = service.ingest_events(
        [
            PurchaseOrderEvent(
                event_id="po:1",
                order_id="PO-1",
                sku="SENSOR-B",
                quantity=25,
                warehouse="WH-SH",
                supplier_id="SUP-BETA",
                created_at="2026-01-15T08:00:00",
                promised_delivery="2026-01-15T20:00:00",
                observed_at="2026-01-15T08:00:00",
                status="shipped",
            ),
            ShipmentEvent(
                event_id="shipment:1",
                shipment_id="SHIP-1",
                order_id="PO-1",
                sku="SENSOR-B",
                warehouse="WH-SH",
                supplier_id="SUP-BETA",
                current_location="Suzhou Hub",
                status="in_transit",
                promised_delivery="2026-01-15T20:00:00",
                estimated_arrival="2026-01-16T10:00:00",
                recorded_at="2026-01-15T12:00:00",
                delay_hours=14.0,
                status_age_hours=10.0,
            ),
        ]
    )

    delayed_alert = next(item for item in result.alerts if item.rule_id == "shipment_delay")

    assert delayed_alert.risk_level == "high"
    assert delayed_alert.affected_order_count == 1
    assert any("加急" in action for action in delayed_alert.recommended_actions)


def test_supplier_recommendations_are_sorted_by_risk(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")

    result = service.ingest_events(
        [
            SupplierPerformanceEvent(
                event_id="supplier:alpha",
                supplier_id="SUP-ALPHA",
                supplier_name="Alpha Components",
                on_time_rate=0.72,
                defect_rate=0.04,
                breach_count_30d=5,
                observed_at="2026-01-15T09:00:00",
            ),
            SupplierPerformanceEvent(
                event_id="supplier:gamma",
                supplier_id="SUP-GAMMA",
                supplier_name="Gamma Electronics",
                on_time_rate=0.98,
                defect_rate=0.008,
                breach_count_30d=0,
                observed_at="2026-01-15T09:01:00",
            ),
            SupplierPerformanceEvent(
                event_id="supplier:beta",
                supplier_id="SUP-BETA",
                supplier_name="Beta Logistics Parts",
                on_time_rate=0.92,
                defect_rate=0.015,
                breach_count_30d=1,
                observed_at="2026-01-15T09:02:00",
            ),
            PurchaseOrderEvent(
                event_id="po:alpha-1",
                order_id="PO-ALPHA-1",
                sku="CHIP-A",
                quantity=70,
                warehouse="WH-SH",
                supplier_id="SUP-ALPHA",
                created_at="2026-01-14T09:00:00",
                promised_delivery="2026-01-16T09:00:00",
                observed_at="2026-01-15T09:03:00",
                status="pending",
            ),
            PurchaseOrderEvent(
                event_id="po:alpha-2",
                order_id="PO-ALPHA-2",
                sku="CHIP-A",
                quantity=30,
                warehouse="WH-SH",
                supplier_id="SUP-ALPHA",
                created_at="2026-01-14T10:00:00",
                promised_delivery="2026-01-16T10:00:00",
                observed_at="2026-01-15T09:04:00",
                status="pending",
            ),
            PurchaseOrderEvent(
                event_id="po:gamma-1",
                order_id="PO-GAMMA-1",
                sku="CHIP-A",
                quantity=10,
                warehouse="WH-SH",
                supplier_id="SUP-GAMMA",
                created_at="2026-01-14T11:00:00",
                promised_delivery="2026-01-16T11:00:00",
                observed_at="2026-01-15T09:05:00",
                status="pending",
            ),
        ]
    )

    concentration_alert = next(
        item for item in result.alerts if item.rule_id == "supplier_concentration"
    )

    assert concentration_alert.alternative_suppliers
    assert concentration_alert.alternative_suppliers[0] == "SUP-GAMMA"


def test_supplier_recommendations_ignore_unrelated_suppliers(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")

    result = service.ingest_events(
        [
            SupplierPerformanceEvent(
                event_id="supplier:alpha",
                supplier_id="SUP-ALPHA",
                supplier_name="Alpha Components",
                on_time_rate=0.72,
                defect_rate=0.04,
                breach_count_30d=5,
                observed_at="2026-01-15T09:00:00",
            ),
            SupplierPerformanceEvent(
                event_id="supplier:gamma",
                supplier_id="SUP-GAMMA",
                supplier_name="Gamma Electronics",
                on_time_rate=0.98,
                defect_rate=0.008,
                breach_count_30d=0,
                observed_at="2026-01-15T09:01:00",
            ),
            SupplierPerformanceEvent(
                event_id="supplier:delta",
                supplier_id="SUP-DELTA",
                supplier_name="Delta Packaging",
                on_time_rate=0.99,
                defect_rate=0.005,
                breach_count_30d=0,
                observed_at="2026-01-15T09:02:00",
            ),
            PurchaseOrderEvent(
                event_id="po:alpha-1",
                order_id="PO-ALPHA-1",
                sku="CHIP-A",
                quantity=60,
                warehouse="WH-SH",
                supplier_id="SUP-ALPHA",
                created_at="2026-01-14T09:00:00",
                promised_delivery="2026-01-16T09:00:00",
                observed_at="2026-01-15T09:03:00",
                status="pending",
            ),
            PurchaseOrderEvent(
                event_id="po:gamma-1",
                order_id="PO-GAMMA-1",
                sku="CHIP-A",
                quantity=10,
                warehouse="WH-SH",
                supplier_id="SUP-GAMMA",
                created_at="2026-01-14T10:00:00",
                promised_delivery="2026-01-16T10:00:00",
                observed_at="2026-01-15T09:04:00",
                status="pending",
            ),
            PurchaseOrderEvent(
                event_id="po:alpha-2",
                order_id="PO-ALPHA-2",
                sku="CHIP-A",
                quantity=30,
                warehouse="WH-SH",
                supplier_id="SUP-ALPHA",
                created_at="2026-01-14T11:00:00",
                promised_delivery="2026-01-16T11:00:00",
                observed_at="2026-01-15T09:05:00",
                status="pending",
            ),
        ]
    )

    concentration_alert = next(
        item for item in result.alerts if item.rule_id == "supplier_concentration"
    )

    assert "SUP-GAMMA" in concentration_alert.alternative_suppliers
    assert "SUP-DELTA" not in concentration_alert.alternative_suppliers
