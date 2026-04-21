from fastapi.testclient import TestClient

from sage.apps.ticket_triage import TicketTriageApplicationService, create_fastapi_app
from sage.apps.ticket_triage.demo_data import build_demo_tickets


def test_api_root_and_health_routes(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")
    client = TestClient(create_fastapi_app(service))

    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json()["name"] == "SAGE Ticket Triage MVP"
    assert "/docs" in root_response.json()["routes"]
    assert "/redoc" in root_response.json()["routes"]
    assert "/dashboard" in root_response.json()["routes"]
    assert "/dashboard/ui" in root_response.json()["routes"]
    assert "/tickets" in root_response.json()["routes"]
    assert "/tickets/ingest" in root_response.json()["routes"]
    assert "/demo/reset-and-run" in root_response.json()["routes"]
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}


def test_api_demo_and_query_routes(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")
    client = TestClient(create_fastapi_app(service))

    demo_response = client.post("/demo/reset-and-run")
    dashboard_response = client.get("/dashboard")
    tickets_response = client.get("/tickets")
    queues_response = client.get("/queues")
    high_priority_response = client.get("/tickets/high-priority")
    ticket_response = client.get("/tickets/T-1001")

    assert demo_response.status_code == 200
    payload = demo_response.json()
    assert payload["processed_event_count"] == 10
    assert payload["high_priority_count"] >= 5

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["total_ticket_count"] == 10
    assert dashboard_response.json()["high_priority_count"] >= 5

    assert tickets_response.status_code == 200
    assert len(tickets_response.json()) == 10

    assert queues_response.status_code == 200
    assert queues_response.json()

    assert high_priority_response.status_code == 200
    assert high_priority_response.json()
    assert all(item["priority"] in {"high", "critical"} for item in high_priority_response.json())

    assert ticket_response.status_code == 200
    assert ticket_response.json()["ticket_id"] == "T-1001"


def test_api_ingest_route_and_missing_ticket(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")
    client = TestClient(create_fastapi_app(service))

    ingest_response = client.post(
        "/tickets/ingest",
        json=[item.to_dict() for item in build_demo_tickets()[:2]],
    )
    missing_response = client.get("/tickets/NOT-FOUND")

    assert ingest_response.status_code == 200
    assert ingest_response.json()["processed_event_count"] == 2

    assert missing_response.status_code == 404
    assert "No ticket found" in missing_response.json()["detail"]


def test_api_dashboard_ui_route(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")
    client = TestClient(create_fastapi_app(service))

    response = client.get("/dashboard/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "客服工单分诊看板" in response.text
    assert "加载演示数据" in response.text
    assert "提交单条工单" in response.text