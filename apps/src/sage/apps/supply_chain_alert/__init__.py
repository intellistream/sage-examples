"""Supply chain alert dashboard MVP built on top of SAGE stateful workflows."""

from .demo_data import build_demo_event_summary, build_demo_supply_events
from .llm import SupplyChainGatewaySettings, SupplyChainRiskExplainer
from .models import (
    AlertExplanation,
    DashboardSnapshot,
    GatewayExplanationStatus,
    InventoryEvent,
    OpenAlert,
    PurchaseOrderEvent,
    RiskExplanationResult,
    ShipmentEvent,
    SupplierPerformanceEvent,
    SupplierRiskSummary,
    SupplyChainRunResult,
)
from .service import (
    SupplyChainAlertApplicationService,
    create_demo_application_service,
    create_fastapi_app,
)

__all__ = [
    "AlertExplanation",
    "DashboardSnapshot",
    "GatewayExplanationStatus",
    "InventoryEvent",
    "OpenAlert",
    "PurchaseOrderEvent",
    "RiskExplanationResult",
    "ShipmentEvent",
    "SupplyChainGatewaySettings",
    "SupplierPerformanceEvent",
    "SupplyChainRiskExplainer",
    "SupplierRiskSummary",
    "SupplyChainAlertApplicationService",
    "SupplyChainRunResult",
    "build_demo_event_summary",
    "build_demo_supply_events",
    "create_demo_application_service",
    "create_fastapi_app",
]