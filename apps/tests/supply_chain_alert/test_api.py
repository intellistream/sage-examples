from fastapi.testclient import TestClient

from sage.apps.supply_chain_alert import (
    GatewayExplanationStatus,
    RiskExplanationResult,
    SupplyChainAlertApplicationService,
    create_fastapi_app,
)
from sage.apps.supply_chain_alert.demo_data import build_demo_supply_events


def test_api_health_and_root(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    client = TestClient(create_fastapi_app(service))

    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json()["name"] == "SAGE Supply Chain Alert Dashboard"
    assert "/dashboard" in root_response.json()["routes"]
    assert "/dashboard/ui" in root_response.json()["routes"]
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}


def test_api_dashboard_ui_route(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    client = TestClient(create_fastapi_app(service))

    response = client.get("/dashboard/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "供应链异常预警看板" in response.text
    assert "加载演示数据" in response.text
    assert "运营总控" in response.text
    assert "采购协调" in response.text
    assert "仓配调度" in response.text
    assert "供应商管理" in response.text
    assert "角色摘要" in response.text
    assert "/alerts/explanations?max_alerts=3" in response.text


def test_api_demo_and_query_routes(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    client = TestClient(create_fastapi_app(service))

    demo_response = client.post("/demo/reset-and-run")
    dashboard_response = client.get("/dashboard")
    alerts_response = client.get("/alerts/open")
    suppliers_response = client.get("/suppliers/risk")

    assert demo_response.status_code == 200
    demo_payload = demo_response.json()
    assert demo_payload["processed_event_count"] == 10
    assert demo_payload["alert_count"] >= 5

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["open_alert_count"] == demo_payload["alert_count"]

    assert alerts_response.status_code == 200
    assert len(alerts_response.json()) == demo_payload["alert_count"]

    assert suppliers_response.status_code == 200
    assert suppliers_response.json()
    assert suppliers_response.json()[0]["supplier_id"] == "SUP-ALPHA"


def test_api_ingest_events_route(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    client = TestClient(create_fastapi_app(service))

    payload = [item.to_dict() for item in build_demo_supply_events()[:3]]
    response = client.post("/events/ingest", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["processed_event_count"] == 3
    assert body["dashboard"]["open_alert_count"] >= 1


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
            dashboard_summary="当前整体风险集中在库存缺口与供应商集中度。",
            alert_explanations=[],
        )


def test_api_explanations_route(tmp_path) -> None:
    service = SupplyChainAlertApplicationService(
        storage_path=tmp_path / "supply-chain-state.json",
        risk_explainer=FakeRiskExplainer(),
    )
    service.run_demo(reset=True)
    client = TestClient(create_fastapi_app(service))

    response = client.get("/alerts/explanations")

    assert response.status_code == 200
    body = response.json()
    assert body["gateway_status"]["reachable"] is True
    assert body["dashboard_summary"]
