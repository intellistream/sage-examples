"""Structured models for the supply chain alert dashboard MVP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, TypeAlias


@dataclass(frozen=True)
class PurchaseOrderEvent:
    event_id: str
    order_id: str
    sku: str
    quantity: int
    warehouse: str
    supplier_id: str
    created_at: str
    promised_delivery: str
    observed_at: str
    status: str = "pending"
    priority: str = "standard"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PurchaseOrderEvent:
        created_at = str(data.get("created_at", data.get("observed_at", "")))
        observed_at = str(data.get("observed_at", created_at))
        return cls(
            event_id=str(data.get("event_id", f"po:{data['order_id']}:{observed_at}")),
            order_id=str(data["order_id"]),
            sku=str(data["sku"]),
            quantity=int(data["quantity"]),
            warehouse=str(data["warehouse"]),
            supplier_id=str(data["supplier_id"]),
            created_at=created_at,
            promised_delivery=str(data["promised_delivery"]),
            observed_at=observed_at,
            status=str(data.get("status", "pending")),
            priority=str(data.get("priority", "standard")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InventoryEvent:
    event_id: str
    sku: str
    warehouse: str
    current_stock: int
    safety_stock: int
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InventoryEvent:
        updated_at = str(data["updated_at"])
        return cls(
            event_id=str(data.get("event_id", f"inventory:{data['warehouse']}:{data['sku']}:{updated_at}")),
            sku=str(data["sku"]),
            warehouse=str(data["warehouse"]),
            current_stock=int(data["current_stock"]),
            safety_stock=int(data["safety_stock"]),
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShipmentEvent:
    event_id: str
    shipment_id: str
    order_id: str
    sku: str
    warehouse: str
    supplier_id: str
    current_location: str
    status: str
    promised_delivery: str
    estimated_arrival: str
    recorded_at: str
    delay_hours: float = 0.0
    status_age_hours: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShipmentEvent:
        recorded_at = str(data["recorded_at"])
        return cls(
            event_id=str(data.get("event_id", f"shipment:{data['shipment_id']}:{recorded_at}")),
            shipment_id=str(data["shipment_id"]),
            order_id=str(data["order_id"]),
            sku=str(data["sku"]),
            warehouse=str(data["warehouse"]),
            supplier_id=str(data["supplier_id"]),
            current_location=str(data.get("current_location", "unknown")),
            status=str(data.get("status", "in_transit")),
            promised_delivery=str(data["promised_delivery"]),
            estimated_arrival=str(data["estimated_arrival"]),
            recorded_at=recorded_at,
            delay_hours=float(data.get("delay_hours", 0.0)),
            status_age_hours=float(data.get("status_age_hours", 0.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SupplierPerformanceEvent:
    event_id: str
    supplier_id: str
    supplier_name: str
    on_time_rate: float
    defect_rate: float
    breach_count_30d: int
    observed_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplierPerformanceEvent:
        observed_at = str(data["observed_at"])
        return cls(
            event_id=str(data.get("event_id", f"supplier:{data['supplier_id']}:{observed_at}")),
            supplier_id=str(data["supplier_id"]),
            supplier_name=str(data.get("supplier_name", data["supplier_id"])),
            on_time_rate=float(data["on_time_rate"]),
            defect_rate=float(data.get("defect_rate", 0.0)),
            breach_count_30d=int(data.get("breach_count_30d", 0)),
            observed_at=observed_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SupplyEvent: TypeAlias = (
    PurchaseOrderEvent | InventoryEvent | ShipmentEvent | SupplierPerformanceEvent
)


def coerce_supply_event(data: SupplyEvent | dict[str, Any]) -> SupplyEvent:
    if isinstance(
        data,
        (PurchaseOrderEvent, InventoryEvent, ShipmentEvent, SupplierPerformanceEvent),
    ):
        return data
    if "shipment_id" in data:
        return ShipmentEvent.from_dict(data)
    if "current_stock" in data:
        return InventoryEvent.from_dict(data)
    if "on_time_rate" in data:
        return SupplierPerformanceEvent.from_dict(data)
    if "order_id" in data and "quantity" in data:
        return PurchaseOrderEvent.from_dict(data)
    raise ValueError(f"Unsupported supply event payload: {data}")


def supply_event_timestamp(event: SupplyEvent) -> str:
    if isinstance(event, PurchaseOrderEvent):
        return event.observed_at
    if isinstance(event, InventoryEvent):
        return event.updated_at
    if isinstance(event, ShipmentEvent):
        return event.recorded_at
    return event.observed_at


@dataclass(frozen=True)
class NormalizedSupplyEvent:
    event_id: str
    event_type: str
    timestamp: str
    payload: dict[str, Any]
    order_id: str | None = None
    sku: str | None = None
    warehouse: str | None = None
    supplier_id: str | None = None
    shipment_id: str | None = None

    @classmethod
    def from_event(cls, event: SupplyEvent) -> NormalizedSupplyEvent:
        if isinstance(event, PurchaseOrderEvent):
            return cls(
                event_id=event.event_id,
                event_type="purchase_order",
                timestamp=event.observed_at,
                payload=event.to_dict(),
                order_id=event.order_id,
                sku=event.sku,
                warehouse=event.warehouse,
                supplier_id=event.supplier_id,
            )
        if isinstance(event, InventoryEvent):
            return cls(
                event_id=event.event_id,
                event_type="inventory",
                timestamp=event.updated_at,
                payload=event.to_dict(),
                sku=event.sku,
                warehouse=event.warehouse,
            )
        if isinstance(event, ShipmentEvent):
            return cls(
                event_id=event.event_id,
                event_type="shipment",
                timestamp=event.recorded_at,
                payload=event.to_dict(),
                order_id=event.order_id,
                sku=event.sku,
                warehouse=event.warehouse,
                supplier_id=event.supplier_id,
                shipment_id=event.shipment_id,
            )
        return cls(
            event_id=event.event_id,
            event_type="supplier_performance",
            timestamp=event.observed_at,
            payload=event.to_dict(),
            supplier_id=event.supplier_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnomalySignal:
    rule_id: str
    title: str
    description: str
    risk_level: str
    triggered_at: str
    source_event_id: str
    order_id: str | None = None
    sku: str | None = None
    warehouse: str | None = None
    supplier_id: str | None = None
    shipment_id: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ImpactAssessment:
    rule_id: str
    risk_level: str
    affected_order_count: int
    affected_sku_count: int
    estimated_stockout_days: float
    impact_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MitigationSuggestion:
    rule_id: str
    actions: list[str]
    rationale: str
    alternative_suppliers: list[str] = field(default_factory=list)
    transfer_warehouse: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpenAlert:
    alert_id: str
    rule_id: str
    title: str
    summary: str
    risk_level: str
    triggered_at: str
    order_id: str | None = None
    sku: str | None = None
    warehouse: str | None = None
    supplier_id: str | None = None
    shipment_id: str | None = None
    affected_order_count: int = 0
    affected_sku_count: int = 0
    estimated_stockout_days: float = 0.0
    recommended_actions: list[str] = field(default_factory=list)
    alternative_suppliers: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenAlert:
        return cls(
            alert_id=str(data["alert_id"]),
            rule_id=str(data["rule_id"]),
            title=str(data["title"]),
            summary=str(data["summary"]),
            risk_level=str(data["risk_level"]),
            triggered_at=str(data["triggered_at"]),
            order_id=data.get("order_id"),
            sku=data.get("sku"),
            warehouse=data.get("warehouse"),
            supplier_id=data.get("supplier_id"),
            shipment_id=data.get("shipment_id"),
            affected_order_count=int(data.get("affected_order_count", 0)),
            affected_sku_count=int(data.get("affected_sku_count", 0)),
            estimated_stockout_days=float(data.get("estimated_stockout_days", 0.0)),
            recommended_actions=list(data.get("recommended_actions", [])),
            alternative_suppliers=list(data.get("alternative_suppliers", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SupplierRiskSummary:
    supplier_id: str
    supplier_name: str
    risk_score: float
    on_time_rate: float
    defect_rate: float
    breach_count_30d: int
    open_alert_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplierRiskSummary:
        return cls(
            supplier_id=str(data["supplier_id"]),
            supplier_name=str(data["supplier_name"]),
            risk_score=float(data["risk_score"]),
            on_time_rate=float(data["on_time_rate"]),
            defect_rate=float(data["defect_rate"]),
            breach_count_30d=int(data["breach_count_30d"]),
            open_alert_count=int(data.get("open_alert_count", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardSnapshot:
    generated_at: str
    open_alert_count: int
    high_risk_alert_count: int
    low_stock_sku_count: int
    delayed_shipment_count: int
    overdue_order_count: int
    high_risk_supplier_count: int
    average_delay_hours: float
    reallocation_suggestion_count: int
    substitute_supplier_suggestion_count: int
    impacted_order_count: int
    top_risk_suppliers: list[SupplierRiskSummary] = field(default_factory=list)
    top_shortage_skus: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "open_alert_count": self.open_alert_count,
            "high_risk_alert_count": self.high_risk_alert_count,
            "low_stock_sku_count": self.low_stock_sku_count,
            "delayed_shipment_count": self.delayed_shipment_count,
            "overdue_order_count": self.overdue_order_count,
            "high_risk_supplier_count": self.high_risk_supplier_count,
            "average_delay_hours": self.average_delay_hours,
            "reallocation_suggestion_count": self.reallocation_suggestion_count,
            "substitute_supplier_suggestion_count": self.substitute_supplier_suggestion_count,
            "impacted_order_count": self.impacted_order_count,
            "top_risk_suppliers": [item.to_dict() for item in self.top_risk_suppliers],
            "top_shortage_skus": list(self.top_shortage_skus),
        }


@dataclass(frozen=True)
class GatewayExplanationStatus:
    reachable: bool
    base_url: str
    health_url: str
    model: str | None = None
    status_code: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlertExplanation:
    alert_id: str
    rule_id: str
    title: str
    risk_level: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskExplanationResult:
    generated_at: str
    gateway_status: GatewayExplanationStatus
    dashboard_summary: str | None = None
    alert_explanations: list[AlertExplanation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "gateway_status": self.gateway_status.to_dict(),
            "dashboard_summary": self.dashboard_summary,
            "alert_explanations": [item.to_dict() for item in self.alert_explanations],
        }


@dataclass(frozen=True)
class SupplyChainRunResult:
    processed_event_count: int
    alert_count: int
    alerts: list[OpenAlert]
    dashboard: DashboardSnapshot
    supplier_risk_summaries: list[SupplierRiskSummary]

    def to_dict(self) -> dict[str, Any]:
        return {
            "processed_event_count": self.processed_event_count,
            "alert_count": self.alert_count,
            "alerts": [item.to_dict() for item in self.alerts],
            "dashboard": self.dashboard.to_dict(),
            "supplier_risk_summaries": [item.to_dict() for item in self.supplier_risk_summaries],
        }