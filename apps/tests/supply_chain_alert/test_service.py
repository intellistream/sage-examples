from sage.apps.supply_chain_alert import (
    GatewayExplanationStatus,
    RiskExplanationResult,
    SupplyChainAlertApplicationService,
)
from sage.apps.supply_chain_alert.demo_data import build_demo_supply_events


def test_state_persists_across_service_instances(tmp_path) -> None:
    storage_path = tmp_path / "supply-chain-state.json"
    first_service = SupplyChainAlertApplicationService(storage_path=storage_path)

    first_result = first_service.ingest_events(build_demo_supply_events())

    second_service = SupplyChainAlertApplicationService(storage_path=storage_path)
    dashboard = second_service.get_dashboard()
    alerts = second_service.list_open_alerts()

    assert dashboard.open_alert_count == first_result.dashboard.open_alert_count
    assert len(alerts) == first_result.alert_count


def test_run_demo_resets_previous_state_by_default(tmp_path) -> None:
    storage_path = tmp_path / "supply-chain-state.json"
    service = SupplyChainAlertApplicationService(storage_path=storage_path)

    first_result = service.run_demo(reset=True)
    second_result = service.run_demo(reset=True)

    assert first_result.alert_count == second_result.alert_count
    assert service.get_dashboard().open_alert_count == second_result.alert_count


class FakeRiskExplainer:
    def explain_current_risks(self, *, dashboard, alerts, supplier_risk_summaries, max_alerts=5):
        return RiskExplanationResult(
            generated_at=dashboard.generated_at,
            gateway_status=GatewayExplanationStatus(
                reachable=True,
                base_url="http://127.0.0.1:19000/v1",
                health_url="http://127.0.0.1:19000/health",
                model="demo-model",
            ),
            dashboard_summary="当前风险以单一供应商依赖和低库存为主。",
            alert_explanations=[],
        )


def test_service_can_return_gateway_explanations(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(
        storage_path=tmp_path / "supply-chain-state.json",
        risk_explainer=FakeRiskExplainer(),
    )
    service.run_demo(reset=True)

    result = service.explain_current_risks(max_alerts=3)

    assert result.gateway_status.reachable is True
    assert "低库存" in result.dashboard_summary
