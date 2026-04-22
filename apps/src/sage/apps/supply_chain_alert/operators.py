"""SAGE operators for the supply chain alert dashboard MVP."""

from __future__ import annotations

from typing import Any

from sage.foundation import BatchFunction, MapFunction, SinkFunction

from .models import (
    AnomalySignal,
    ImpactAssessment,
    InventoryEvent,
    MitigationSuggestion,
    NormalizedSupplyEvent,
    OpenAlert,
    PurchaseOrderEvent,
    ShipmentEvent,
    SupplierPerformanceEvent,
    coerce_supply_event,
)
from .state_store import parse_timestamp

STATE_SERVICE_NAME = "supply_chain_state"


def _risk_rank(level: str) -> int:
    mapping = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return mapping.get(level, 1)


def _max_risk_level(*levels: str) -> str:
    resolved = max(levels, key=_risk_rank)
    return resolved


class DemoEventSource(BatchFunction):
    """BatchFunction source that emits demo or supplied events one by one."""

    def __init__(self, events: list[Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self.events = list(events)
        self.index = 0

    def execute(self) -> Any | None:
        if self.index >= len(self.events):
            return None
        event = self.events[self.index]
        self.index += 1
        return event


class NormalizeEventStep(MapFunction):
    def execute(
        self,
        data: PurchaseOrderEvent
        | InventoryEvent
        | ShipmentEvent
        | SupplierPerformanceEvent
        | dict[str, Any],
    ) -> NormalizedSupplyEvent:
        event = coerce_supply_event(data)
        return NormalizedSupplyEvent.from_event(event)


class UpdateStateStep(MapFunction):
    def execute(self, data: NormalizedSupplyEvent) -> NormalizedSupplyEvent:
        if data.event_type == "purchase_order":
            self.call_service(
                STATE_SERVICE_NAME,
                PurchaseOrderEvent.from_dict(data.payload),
                method="upsert_purchase_order",
            )
        elif data.event_type == "inventory":
            self.call_service(
                STATE_SERVICE_NAME,
                InventoryEvent.from_dict(data.payload),
                method="upsert_inventory",
            )
        elif data.event_type == "shipment":
            self.call_service(
                STATE_SERVICE_NAME,
                ShipmentEvent.from_dict(data.payload),
                method="upsert_shipment",
            )
        elif data.event_type == "supplier_performance":
            self.call_service(
                STATE_SERVICE_NAME,
                SupplierPerformanceEvent.from_dict(data.payload),
                method="upsert_supplier_performance",
            )
        return data


class DetectAnomalyStep(MapFunction):
    def execute(self, data: NormalizedSupplyEvent) -> dict[str, Any]:
        signals: list[AnomalySignal] = []

        if data.event_type == "inventory":
            signals.extend(self._detect_low_inventory(data))
        elif data.event_type == "purchase_order":
            signals.extend(self._detect_order_backlog(data))
            signals.extend(self._detect_supplier_concentration(data))
        elif data.event_type == "shipment":
            signals.extend(self._detect_shipment_delay(data))
            signals.extend(self._detect_shipment_stagnation(data))
        elif data.event_type == "supplier_performance":
            signals.extend(self._detect_supplier_risk(data))

        return {"event": data, "signals": signals}

    def _detect_low_inventory(self, data: NormalizedSupplyEvent) -> list[AnomalySignal]:
        if data.warehouse is None or data.sku is None:
            return []
        inventory = self.call_service(
            STATE_SERVICE_NAME,
            data.warehouse,
            data.sku,
            method="get_inventory_snapshot",
        )
        if inventory is None or inventory.current_stock >= inventory.safety_stock:
            return []

        shortage = inventory.safety_stock - inventory.current_stock
        ratio = inventory.current_stock / max(inventory.safety_stock, 1)
        risk_level = "high" if ratio < 0.5 else "medium"
        return [
            AnomalySignal(
                rule_id="low_inventory",
                title="安全库存不足",
                description=(
                    f"仓库 {inventory.warehouse} 的 {inventory.sku} 当前库存 {inventory.current_stock}，"
                    f"低于安全库存 {inventory.safety_stock}。"
                ),
                risk_level=risk_level,
                triggered_at=data.timestamp,
                source_event_id=data.event_id,
                sku=inventory.sku,
                warehouse=inventory.warehouse,
                metrics={
                    "current_stock": inventory.current_stock,
                    "safety_stock": inventory.safety_stock,
                    "shortage": shortage,
                },
            )
        ]

    def _detect_order_backlog(self, data: NormalizedSupplyEvent) -> list[AnomalySignal]:
        if data.order_id is None:
            return []
        order = self.call_service(STATE_SERVICE_NAME, data.order_id, method="get_order")
        if order is None:
            return []
        if order.status.lower() in {"fulfilled", "delivered", "cancelled", "shipped"}:
            return []

        is_overdue = parse_timestamp(order.promised_delivery) < parse_timestamp(data.timestamp)
        if not is_overdue:
            return []

        hours_overdue = round(
            (
                parse_timestamp(data.timestamp) - parse_timestamp(order.promised_delivery)
            ).total_seconds()
            / 3600.0,
            2,
        )
        risk_level = "high" if hours_overdue >= 2.0 else "medium"
        return [
            AnomalySignal(
                rule_id="order_backlog",
                title="订单积压",
                description=(
                    f"订单 {order.order_id} 已超过承诺交期 {hours_overdue} 小时，当前状态仍为 {order.status}。"
                ),
                risk_level=risk_level,
                triggered_at=data.timestamp,
                source_event_id=data.event_id,
                order_id=order.order_id,
                sku=order.sku,
                warehouse=order.warehouse,
                supplier_id=order.supplier_id,
                metrics={"hours_overdue": hours_overdue, "quantity": order.quantity},
            )
        ]

    def _detect_supplier_concentration(self, data: NormalizedSupplyEvent) -> list[AnomalySignal]:
        if data.order_id is None:
            return []
        order = self.call_service(STATE_SERVICE_NAME, data.order_id, method="get_order")
        if order is None:
            return []

        open_orders = self.call_service(STATE_SERVICE_NAME, method="get_open_orders")
        same_sku_orders = [item for item in open_orders if item.sku == order.sku]
        total_quantity = sum(item.quantity for item in same_sku_orders)
        supplier_quantity = sum(
            item.quantity for item in same_sku_orders if item.supplier_id == order.supplier_id
        )
        if total_quantity < 80:
            return []

        dependency_ratio = supplier_quantity / max(total_quantity, 1)
        if dependency_ratio < 0.75:
            return []

        risk_level = "high" if dependency_ratio >= 0.85 else "medium"
        return [
            AnomalySignal(
                rule_id="supplier_concentration",
                title="单一供应商依赖过高",
                description=(
                    f"SKU {order.sku} 的未完成采购量中有 {dependency_ratio:.0%} 来自供应商 {order.supplier_id}。"
                ),
                risk_level=risk_level,
                triggered_at=data.timestamp,
                source_event_id=data.event_id,
                order_id=order.order_id,
                sku=order.sku,
                warehouse=order.warehouse,
                supplier_id=order.supplier_id,
                metrics={
                    "dependency_ratio": round(dependency_ratio, 3),
                    "supplier_quantity": supplier_quantity,
                    "total_quantity": total_quantity,
                },
            )
        ]

    def _detect_shipment_delay(self, data: NormalizedSupplyEvent) -> list[AnomalySignal]:
        if data.shipment_id is None:
            return []
        shipment = self.call_service(STATE_SERVICE_NAME, data.shipment_id, method="get_shipment")
        if shipment is None:
            return []
        arrival_late = parse_timestamp(shipment.estimated_arrival) > parse_timestamp(
            shipment.promised_delivery
        )
        if not arrival_late and shipment.delay_hours < 6.0:
            return []

        risk_level = "high" if shipment.delay_hours >= 12.0 else "medium"
        return [
            AnomalySignal(
                rule_id="shipment_delay",
                title="在途延迟",
                description=(
                    f"运单 {shipment.shipment_id} 预计晚于承诺交付，当前延迟 {shipment.delay_hours:.1f} 小时。"
                ),
                risk_level=risk_level,
                triggered_at=data.timestamp,
                source_event_id=data.event_id,
                order_id=shipment.order_id,
                sku=shipment.sku,
                warehouse=shipment.warehouse,
                supplier_id=shipment.supplier_id,
                shipment_id=shipment.shipment_id,
                metrics={"delay_hours": shipment.delay_hours},
            )
        ]

    def _detect_shipment_stagnation(self, data: NormalizedSupplyEvent) -> list[AnomalySignal]:
        if data.shipment_id is None:
            return []
        shipment = self.call_service(STATE_SERVICE_NAME, data.shipment_id, method="get_shipment")
        if shipment is None:
            return []
        if shipment.status.lower() in {"delivered", "completed"} or shipment.status_age_hours < 8.0:
            return []

        risk_level = "high" if shipment.status_age_hours >= 12.0 else "medium"
        return [
            AnomalySignal(
                rule_id="shipment_stagnation",
                title="发货停滞",
                description=(
                    f"运单 {shipment.shipment_id} 状态 {shipment.status} 已持续 {shipment.status_age_hours:.1f} 小时未变化。"
                ),
                risk_level=risk_level,
                triggered_at=data.timestamp,
                source_event_id=data.event_id,
                order_id=shipment.order_id,
                sku=shipment.sku,
                warehouse=shipment.warehouse,
                supplier_id=shipment.supplier_id,
                shipment_id=shipment.shipment_id,
                metrics={"status_age_hours": shipment.status_age_hours},
            )
        ]

    def _detect_supplier_risk(self, data: NormalizedSupplyEvent) -> list[AnomalySignal]:
        if data.supplier_id is None:
            return []
        supplier = self.call_service(
            STATE_SERVICE_NAME,
            data.supplier_id,
            method="get_supplier_profile",
        )
        if supplier is None:
            return []
        risk_score = self.call_service(STATE_SERVICE_NAME, supplier, method="compute_supplier_risk")
        if risk_score < 45.0:
            return []

        risk_level = "high" if risk_score >= 55.0 else "medium"
        return [
            AnomalySignal(
                rule_id="supplier_risk_deterioration",
                title="供应商履约恶化",
                description=(
                    f"供应商 {supplier.supplier_name} 近期准时率降至 {supplier.on_time_rate:.0%}，"
                    f"且 30 天违约 {supplier.breach_count_30d} 次。"
                ),
                risk_level=risk_level,
                triggered_at=data.timestamp,
                source_event_id=data.event_id,
                supplier_id=supplier.supplier_id,
                metrics={
                    "risk_score": risk_score,
                    "on_time_rate": supplier.on_time_rate,
                    "breach_count_30d": supplier.breach_count_30d,
                },
            )
        ]


class AssessImpactStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        event = data["event"]
        signals = list(data["signals"])
        assessments: list[ImpactAssessment] = []
        for signal in signals:
            impacted_orders = self._resolve_impacted_orders(signal)
            estimated_stockout_days = self._estimate_stockout_days(signal)
            risk_level = signal.risk_level
            if len(impacted_orders) >= 2 or estimated_stockout_days >= 2.0:
                risk_level = _max_risk_level(signal.risk_level, "high")
            assessments.append(
                ImpactAssessment(
                    rule_id=signal.rule_id,
                    risk_level=risk_level,
                    affected_order_count=len(impacted_orders),
                    affected_sku_count=1 if signal.sku else 0,
                    estimated_stockout_days=estimated_stockout_days,
                    impact_summary=(
                        f"影响 {len(impacted_orders)} 个订单，预计库存风险窗口 {estimated_stockout_days:.1f} 天。"
                    ),
                )
            )
        return {"event": event, "signals": signals, "assessments": assessments}

    def _resolve_impacted_orders(self, signal: AnomalySignal) -> list[PurchaseOrderEvent]:
        open_orders = self.call_service(STATE_SERVICE_NAME, method="get_open_orders")
        if signal.order_id is not None:
            order = self.call_service(STATE_SERVICE_NAME, signal.order_id, method="get_order")
            return [] if order is None else [order]
        if signal.sku is None:
            return []
        return [
            item
            for item in open_orders
            if item.sku == signal.sku
            and (signal.warehouse is None or item.warehouse == signal.warehouse)
        ]

    def _estimate_stockout_days(self, signal: AnomalySignal) -> float:
        if signal.sku is None or signal.warehouse is None:
            return 0.0
        inventory = self.call_service(
            STATE_SERVICE_NAME,
            signal.warehouse,
            signal.sku,
            method="get_inventory_snapshot",
        )
        if inventory is None:
            return 0.0

        shortage = max(0, inventory.safety_stock - inventory.current_stock)
        if shortage == 0:
            return 0.0
        open_orders = self.call_service(STATE_SERVICE_NAME, method="get_open_orders")
        same_sku_orders = [
            item
            for item in open_orders
            if item.sku == signal.sku and item.warehouse == signal.warehouse
        ]
        daily_demand = max(sum(item.quantity for item in same_sku_orders) / 7.0, 1.0)
        return round(shortage / daily_demand, 2)


class RecommendMitigationStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        alerts: list[OpenAlert] = []
        for signal, assessment in zip(data["signals"], data["assessments"], strict=False):
            suggestion = self._build_suggestion(signal, assessment)
            alert = OpenAlert(
                alert_id=f"{signal.source_event_id}:{signal.rule_id}",
                rule_id=signal.rule_id,
                title=signal.title,
                summary=f"{signal.description} {assessment.impact_summary}",
                risk_level=assessment.risk_level,
                triggered_at=signal.triggered_at,
                order_id=signal.order_id,
                sku=signal.sku,
                warehouse=signal.warehouse,
                supplier_id=signal.supplier_id,
                shipment_id=signal.shipment_id,
                affected_order_count=assessment.affected_order_count,
                affected_sku_count=assessment.affected_sku_count,
                estimated_stockout_days=assessment.estimated_stockout_days,
                recommended_actions=suggestion.actions,
                alternative_suppliers=suggestion.alternative_suppliers,
            )
            self.call_service(STATE_SERVICE_NAME, alert, method="save_alert")
            alerts.append(alert)
        return {"event": data["event"], "alerts": alerts}

    def _build_suggestion(
        self,
        signal: AnomalySignal,
        assessment: ImpactAssessment,
    ) -> MitigationSuggestion:
        actions: list[str] = []
        alternative_suppliers: list[str] = []
        transfer_warehouse: str | None = None

        if signal.rule_id == "low_inventory" and signal.sku and signal.warehouse:
            candidates = self.call_service(
                STATE_SERVICE_NAME,
                signal.sku,
                signal.warehouse,
                method="find_transfer_candidates",
            )
            if candidates:
                transfer_warehouse = candidates[0].warehouse
                actions.append(f"从 {transfer_warehouse} 调拨 {signal.sku} 到 {signal.warehouse}")
            actions.append("对缺口 SKU 发起加急补货")

        if signal.rule_id in {"shipment_delay", "shipment_stagnation"}:
            actions.append("联系承运方加急处理，并重算对客户承诺交期")

        if signal.rule_id == "order_backlog":
            actions.append("将积压订单提升到优先履约队列")

        if (
            signal.rule_id in {"supplier_concentration", "supplier_risk_deterioration"}
            and signal.sku
        ):
            supplier_candidates = self.call_service(
                STATE_SERVICE_NAME,
                signal.sku,
                signal.supplier_id,
                method="list_supplier_candidates_for_sku",
            )
            alternative_suppliers = [item.supplier_id for item in supplier_candidates[:2]]
            if alternative_suppliers:
                actions.append("切换部分后续采购到替代供应商: " + ", ".join(alternative_suppliers))
            actions.append("降低单一供应商采购集中度")

        if not actions:
            actions.append("人工复核当前异常并更新处置计划")

        rationale = (
            f"规则 {signal.rule_id} 当前风险等级为 {assessment.risk_level}，"
            f"影响订单 {assessment.affected_order_count} 个。"
        )
        return MitigationSuggestion(
            rule_id=signal.rule_id,
            actions=actions,
            rationale=rationale,
            alternative_suppliers=alternative_suppliers,
            transfer_warehouse=transfer_warehouse,
        )


class AlertCollectorSink(SinkFunction):
    def __init__(self, results: list[OpenAlert], **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results

    def execute(self, data: dict[str, Any]) -> None:
        self.results.extend(data.get("alerts", []))
