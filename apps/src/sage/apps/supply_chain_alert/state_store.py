"""Explicit in-memory state store for the supply chain alert dashboard."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import (
    DashboardSnapshot,
    InventoryEvent,
    OpenAlert,
    PurchaseOrderEvent,
    ShipmentEvent,
    SupplierPerformanceEvent,
    SupplierRiskSummary,
)


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


class InMemorySupplyChainStateStore:
    """Pluggable in-memory state store with optional JSON persistence."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = None if storage_path is None else Path(storage_path)
        self.inventories: dict[tuple[str, str], InventoryEvent] = {}
        self.orders: dict[str, PurchaseOrderEvent] = {}
        self.shipments: dict[str, ShipmentEvent] = {}
        self.suppliers: dict[str, SupplierPerformanceEvent] = {}
        self.alerts: dict[str, OpenAlert] = {}

        if self.storage_path is not None and self.storage_path.exists():
            self._load()

    def reset(self) -> None:
        self.inventories = {}
        self.orders = {}
        self.shipments = {}
        self.suppliers = {}
        self.alerts = {}
        self._persist()

    def upsert_inventory(self, inventory: InventoryEvent) -> None:
        self.inventories[(inventory.warehouse, inventory.sku)] = inventory
        self._persist()

    def upsert_purchase_order(self, order: PurchaseOrderEvent) -> None:
        self.orders[order.order_id] = order
        self._persist()

    def upsert_shipment(self, shipment: ShipmentEvent) -> None:
        self.shipments[shipment.shipment_id] = shipment
        self._persist()

    def upsert_supplier_performance(self, supplier: SupplierPerformanceEvent) -> None:
        self.suppliers[supplier.supplier_id] = supplier
        self._persist()

    def get_inventory_snapshot(self, warehouse: str, sku: str) -> InventoryEvent | None:
        return self.inventories.get((warehouse, sku))

    def list_inventory_snapshots(self, sku: str | None = None) -> list[InventoryEvent]:
        inventories = list(self.inventories.values())
        if sku is None:
            return inventories
        return [item for item in inventories if item.sku == sku]

    def get_order(self, order_id: str) -> PurchaseOrderEvent | None:
        return self.orders.get(order_id)

    def get_open_orders(self) -> list[PurchaseOrderEvent]:
        closed_statuses = {"fulfilled", "delivered", "cancelled"}
        return [item for item in self.orders.values() if item.status.lower() not in closed_statuses]

    def get_shipment(self, shipment_id: str) -> ShipmentEvent | None:
        return self.shipments.get(shipment_id)

    def list_shipments(self) -> list[ShipmentEvent]:
        return list(self.shipments.values())

    def get_supplier_profile(self, supplier_id: str) -> SupplierPerformanceEvent | None:
        return self.suppliers.get(supplier_id)

    def list_supplier_profiles(self) -> list[SupplierPerformanceEvent]:
        return list(self.suppliers.values())

    def save_alert(self, alert: OpenAlert) -> None:
        self.alerts[alert.alert_id] = alert
        self._persist()

    def list_open_alerts(self) -> list[OpenAlert]:
        return sorted(self.alerts.values(), key=lambda item: item.triggered_at)

    def find_transfer_candidates(self, sku: str, exclude_warehouse: str) -> list[InventoryEvent]:
        candidates = [
            item
            for item in self.list_inventory_snapshots(sku)
            if item.warehouse != exclude_warehouse and item.current_stock > item.safety_stock
        ]
        return sorted(
            candidates,
            key=lambda item: (item.current_stock - item.safety_stock),
            reverse=True,
        )

    def list_supplier_candidates_for_sku(
        self,
        sku: str,
        exclude_supplier_id: str | None = None,
    ) -> list[SupplierRiskSummary]:
        supplier_ids = {item.supplier_id for item in self.get_open_orders() if item.sku == sku}
        if exclude_supplier_id is not None:
            supplier_ids.discard(exclude_supplier_id)

        all_summaries = self.build_supplier_risk_summary(limit=None)
        if supplier_ids:
            summaries = [summary for summary in all_summaries if summary.supplier_id in supplier_ids]
        elif exclude_supplier_id is not None:
            summaries = [
                summary for summary in all_summaries if summary.supplier_id != exclude_supplier_id
            ]
        else:
            summaries = list(all_summaries)

        return sorted(summaries, key=lambda item: item.risk_score)

    def compute_supplier_risk(self, supplier: SupplierPerformanceEvent) -> float:
        lateness_risk = (1.0 - supplier.on_time_rate) * 55.0
        defect_risk = supplier.defect_rate * 100.0 * 1.2
        breach_risk = float(supplier.breach_count_30d) * 6.0
        return round(min(100.0, lateness_risk + defect_risk + breach_risk), 2)

    def build_supplier_risk_summary(self, limit: int | None = 5) -> list[SupplierRiskSummary]:
        alerts_by_supplier: dict[str, int] = {}
        for alert in self.alerts.values():
            if alert.supplier_id is None:
                continue
            alerts_by_supplier[alert.supplier_id] = alerts_by_supplier.get(alert.supplier_id, 0) + 1

        summaries = [
            SupplierRiskSummary(
                supplier_id=item.supplier_id,
                supplier_name=item.supplier_name,
                risk_score=self.compute_supplier_risk(item),
                on_time_rate=item.on_time_rate,
                defect_rate=item.defect_rate,
                breach_count_30d=item.breach_count_30d,
                open_alert_count=alerts_by_supplier.get(item.supplier_id, 0),
            )
            for item in self.suppliers.values()
        ]
        summaries.sort(key=lambda item: item.risk_score, reverse=True)
        return summaries if limit is None else summaries[:limit]

    def build_dashboard_snapshot(self, as_of: str | None = None) -> DashboardSnapshot:
        resolved_as_of = as_of or self._infer_latest_timestamp()
        snapshot_time = parse_timestamp(resolved_as_of)
        open_alerts = self.list_open_alerts()
        open_orders = self.get_open_orders()
        delayed_shipments = [item for item in self.shipments.values() if item.delay_hours > 0.0]
        overdue_orders = [
            item for item in open_orders if parse_timestamp(item.promised_delivery) < snapshot_time
        ]
        low_stock_items = [
            item for item in self.inventories.values() if item.current_stock < item.safety_stock
        ]
        top_shortage_skus = [
            item.sku
            for item in sorted(
                low_stock_items,
                key=lambda inventory: (inventory.safety_stock - inventory.current_stock),
                reverse=True,
            )
        ][:3]
        supplier_risk = self.build_supplier_risk_summary(limit=3)
        average_delay = 0.0
        if delayed_shipments:
            average_delay = round(
                sum(item.delay_hours for item in delayed_shipments) / len(delayed_shipments),
                2,
            )

        impacted_orders = {
            alert.order_id for alert in open_alerts if alert.order_id is not None
        }
        impacted_orders.update(
            order.order_id
            for order in overdue_orders
            if any(alert.sku == order.sku for alert in open_alerts if alert.sku is not None)
        )

        return DashboardSnapshot(
            generated_at=resolved_as_of,
            open_alert_count=len(open_alerts),
            high_risk_alert_count=sum(
                1 for item in open_alerts if item.risk_level in {"high", "critical"}
            ),
            low_stock_sku_count=len(low_stock_items),
            delayed_shipment_count=len(delayed_shipments),
            overdue_order_count=len(overdue_orders),
            high_risk_supplier_count=sum(1 for item in supplier_risk if item.risk_score >= 45.0),
            average_delay_hours=average_delay,
            reallocation_suggestion_count=sum(
                1
                for item in open_alerts
                if any("调拨" in action or "transfer" in action for action in item.recommended_actions)
            ),
            substitute_supplier_suggestion_count=sum(
                1 for item in open_alerts if item.alternative_suppliers
            ),
            impacted_order_count=len(impacted_orders),
            top_risk_suppliers=supplier_risk,
            top_shortage_skus=top_shortage_skus,
        )

    def _infer_latest_timestamp(self) -> str:
        timestamps: list[str] = []
        timestamps.extend(item.updated_at for item in self.inventories.values())
        timestamps.extend(item.observed_at for item in self.orders.values())
        timestamps.extend(item.recorded_at for item in self.shipments.values())
        timestamps.extend(item.observed_at for item in self.suppliers.values())
        timestamps.extend(item.triggered_at for item in self.alerts.values())
        if not timestamps:
            return datetime.utcnow().replace(microsecond=0).isoformat()
        return max(timestamps)

    def _persist(self) -> None:
        if self.storage_path is None:
            return

        if self.storage_path.parent and not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "inventories": [item.to_dict() for item in self.inventories.values()],
            "orders": [item.to_dict() for item in self.orders.values()],
            "shipments": [item.to_dict() for item in self.shipments.values()],
            "suppliers": [item.to_dict() for item in self.suppliers.values()],
            "alerts": [item.to_dict() for item in self.alerts.values()],
        }
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if self.storage_path is None:
            return

        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self.inventories = {
            (item["warehouse"], item["sku"]): InventoryEvent.from_dict(item)
            for item in payload.get("inventories", [])
        }
        self.orders = {
            item["order_id"]: PurchaseOrderEvent.from_dict(item)
            for item in payload.get("orders", [])
        }
        self.shipments = {
            item["shipment_id"]: ShipmentEvent.from_dict(item)
            for item in payload.get("shipments", [])
        }
        self.suppliers = {
            item["supplier_id"]: SupplierPerformanceEvent.from_dict(item)
            for item in payload.get("suppliers", [])
        }
        self.alerts = {
            item["alert_id"]: OpenAlert.from_dict(item) for item in payload.get("alerts", [])
        }