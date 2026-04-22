"""SAGE workflow orchestration for the supply chain alert dashboard MVP."""

from __future__ import annotations

from pathlib import Path

from sage.runtime import BaseService, LocalEnvironment

from .models import DashboardSnapshot, OpenAlert, SupplierRiskSummary, SupplyEvent
from .operators import (
    STATE_SERVICE_NAME,
    AlertCollectorSink,
    AssessImpactStep,
    DemoEventSource,
    DetectAnomalyStep,
    NormalizeEventStep,
    RecommendMitigationStep,
    UpdateStateStep,
)
from .state_store import InMemorySupplyChainStateStore


class SupplyChainStateService(BaseService):
    """Runtime service exposing explicit state operations to workflow nodes."""

    def __init__(self, store: InMemorySupplyChainStateStore) -> None:
        super().__init__()
        self.store = store

    def reset(self) -> None:
        self.store.reset()

    def upsert_inventory(self, inventory) -> None:
        self.store.upsert_inventory(inventory)

    def upsert_purchase_order(self, order) -> None:
        self.store.upsert_purchase_order(order)

    def upsert_shipment(self, shipment) -> None:
        self.store.upsert_shipment(shipment)

    def upsert_supplier_performance(self, supplier) -> None:
        self.store.upsert_supplier_performance(supplier)

    def get_inventory_snapshot(self, warehouse: str, sku: str):
        return self.store.get_inventory_snapshot(warehouse, sku)

    def get_order(self, order_id: str):
        return self.store.get_order(order_id)

    def get_open_orders(self):
        return self.store.get_open_orders()

    def get_shipment(self, shipment_id: str):
        return self.store.get_shipment(shipment_id)

    def get_supplier_profile(self, supplier_id: str):
        return self.store.get_supplier_profile(supplier_id)

    def compute_supplier_risk(self, supplier) -> float:
        return self.store.compute_supplier_risk(supplier)

    def find_transfer_candidates(self, sku: str, exclude_warehouse: str):
        return self.store.find_transfer_candidates(sku, exclude_warehouse)

    def list_supplier_candidates_for_sku(self, sku: str, exclude_supplier_id: str | None = None):
        return self.store.list_supplier_candidates_for_sku(sku, exclude_supplier_id)

    def save_alert(self, alert) -> None:
        self.store.save_alert(alert)

    def list_open_alerts(self) -> list[OpenAlert]:
        return self.store.list_open_alerts()

    def build_dashboard_snapshot(self, as_of: str | None = None) -> DashboardSnapshot:
        return self.store.build_dashboard_snapshot(as_of=as_of)

    def build_supplier_risk_summary(self, limit: int | None = 5) -> list[SupplierRiskSummary]:
        return self.store.build_supplier_risk_summary(limit=limit)


class SupplyChainWorkflowRunner:
    """Thin workflow runner that rebuilds a LocalEnvironment per ingest operation."""

    def __init__(self, state_store: InMemorySupplyChainStateStore | None = None) -> None:
        self.state_store = state_store or InMemorySupplyChainStateStore()

    @classmethod
    def from_storage_path(cls, storage_path: str | Path | None = None) -> SupplyChainWorkflowRunner:
        return cls(InMemorySupplyChainStateStore(storage_path=storage_path))

    def _build_environment(self, name: str) -> LocalEnvironment:
        environment = LocalEnvironment(name)
        environment.set_console_log_level("ERROR")
        environment.register_service(STATE_SERVICE_NAME, SupplyChainStateService, self.state_store)
        return environment

    def reset(self) -> None:
        self.state_store.reset()

    def ingest_events(self, events: list[SupplyEvent | dict]) -> list[OpenAlert]:
        results: list[OpenAlert] = []
        environment = self._build_environment("supply_chain_alert_ingest")
        (
            environment.from_batch(DemoEventSource, events=events)
            .map(NormalizeEventStep)
            .map(UpdateStateStep)
            .map(DetectAnomalyStep)
            .map(AssessImpactStep)
            .map(RecommendMitigationStep)
            .sink(AlertCollectorSink, results=results)
        )
        environment.submit(autostop=True)
        return results

    def get_dashboard(self, as_of: str | None = None) -> DashboardSnapshot:
        return self.state_store.build_dashboard_snapshot(as_of=as_of)

    def list_open_alerts(self) -> list[OpenAlert]:
        return self.state_store.list_open_alerts()

    def list_supplier_risk_summary(self, limit: int | None = 5) -> list[SupplierRiskSummary]:
        return self.state_store.build_supplier_risk_summary(limit=limit)
