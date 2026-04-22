"""Demo data for the supply chain alert dashboard MVP."""

from __future__ import annotations

from .models import (
    InventoryEvent,
    PurchaseOrderEvent,
    ShipmentEvent,
    SupplierPerformanceEvent,
    SupplyEvent,
)


def build_demo_supply_events() -> list[SupplyEvent]:
    return [
        InventoryEvent(
            event_id="inventory:wh-sh:chip-a:2026-01-15T09:00:00",
            sku="CHIP-A",
            warehouse="WH-SH",
            current_stock=18,
            safety_stock=40,
            updated_at="2026-01-15T09:00:00",
        ),
        InventoryEvent(
            event_id="inventory:wh-bj:chip-a:2026-01-15T09:03:00",
            sku="CHIP-A",
            warehouse="WH-BJ",
            current_stock=120,
            safety_stock=30,
            updated_at="2026-01-15T09:03:00",
        ),
        SupplierPerformanceEvent(
            event_id="supplier:alpha:2026-01-15T09:05:00",
            supplier_id="SUP-ALPHA",
            supplier_name="Alpha Components",
            on_time_rate=0.72,
            defect_rate=0.035,
            breach_count_30d=5,
            observed_at="2026-01-15T09:05:00",
        ),
        SupplierPerformanceEvent(
            event_id="supplier:beta:2026-01-15T09:06:00",
            supplier_id="SUP-BETA",
            supplier_name="Beta Logistics Parts",
            on_time_rate=0.91,
            defect_rate=0.018,
            breach_count_30d=1,
            observed_at="2026-01-15T09:06:00",
        ),
        SupplierPerformanceEvent(
            event_id="supplier:gamma:2026-01-15T09:07:00",
            supplier_id="SUP-GAMMA",
            supplier_name="Gamma Electronics",
            on_time_rate=0.97,
            defect_rate=0.008,
            breach_count_30d=0,
            observed_at="2026-01-15T09:07:00",
        ),
        PurchaseOrderEvent(
            event_id="po:1001:2026-01-15T21:30:00",
            order_id="PO-1001",
            sku="CHIP-A",
            quantity=60,
            warehouse="WH-SH",
            supplier_id="SUP-ALPHA",
            created_at="2026-01-14T08:30:00",
            promised_delivery="2026-01-15T18:00:00",
            observed_at="2026-01-15T21:30:00",
            status="pending",
            priority="high",
        ),
        PurchaseOrderEvent(
            event_id="po:1002:2026-01-15T21:31:00",
            order_id="PO-1002",
            sku="CHIP-A",
            quantity=40,
            warehouse="WH-SH",
            supplier_id="SUP-ALPHA",
            created_at="2026-01-14T09:00:00",
            promised_delivery="2026-01-15T20:00:00",
            observed_at="2026-01-15T21:31:00",
            status="pending",
            priority="high",
        ),
        PurchaseOrderEvent(
            event_id="po:1003:2026-01-15T13:00:00",
            order_id="PO-1003",
            sku="CHIP-A",
            quantity=10,
            warehouse="WH-SH",
            supplier_id="SUP-GAMMA",
            created_at="2026-01-15T13:00:00",
            promised_delivery="2026-01-16T12:00:00",
            observed_at="2026-01-15T13:00:00",
            status="confirmed",
            priority="standard",
        ),
        PurchaseOrderEvent(
            event_id="po:2001:2026-01-15T10:15:00",
            order_id="PO-2001",
            sku="SENSOR-B",
            quantity=25,
            warehouse="WH-SH",
            supplier_id="SUP-BETA",
            created_at="2026-01-15T10:15:00",
            promised_delivery="2026-01-15T22:00:00",
            observed_at="2026-01-15T10:15:00",
            status="shipped",
            priority="standard",
        ),
        ShipmentEvent(
            event_id="shipment:9001:2026-01-15T10:45:00",
            shipment_id="SHIP-9001",
            order_id="PO-2001",
            sku="SENSOR-B",
            warehouse="WH-SH",
            supplier_id="SUP-BETA",
            current_location="Nanjing Transfer Hub",
            status="in_transit",
            promised_delivery="2026-01-15T22:00:00",
            estimated_arrival="2026-01-16T10:00:00",
            recorded_at="2026-01-15T10:45:00",
            delay_hours=12.0,
            status_age_hours=9.5,
        ),
    ]


def build_demo_event_summary() -> dict[str, int]:
    events = build_demo_supply_events()
    warehouses = {
        event.warehouse for event in events if hasattr(event, "warehouse") and event.warehouse
    }
    suppliers = {
        event.supplier_id for event in events if hasattr(event, "supplier_id") and event.supplier_id
    }
    orders = {event.order_id for event in events if isinstance(event, PurchaseOrderEvent)}
    return {
        "warehouse_count": len(warehouses),
        "supplier_count": len(suppliers),
        "order_count": len(orders),
        "event_count": len(events),
    }
