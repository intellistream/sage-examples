from sage.apps.ticket_triage import TicketTriageApplicationService
from sage.apps.ticket_triage.demo_data import build_demo_tickets


def test_state_persists_across_service_instances(tmp_path) -> None:
    storage_path = tmp_path / "ticket-state.json"
    first_service = TicketTriageApplicationService(storage_path=storage_path)

    first_result = first_service.ingest_tickets(build_demo_tickets())

    second_service = TicketTriageApplicationService(storage_path=storage_path)
    queue_summary = second_service.list_queue_summary()
    snapshot = second_service.get_ticket("T-1001")

    assert (
        sum(item.open_ticket_count for item in queue_summary) == first_result.processed_event_count
    )
    assert snapshot.intent == "login_issue"


def test_run_demo_resets_previous_state_by_default(tmp_path) -> None:
    storage_path = tmp_path / "ticket-state.json"
    service = TicketTriageApplicationService(storage_path=storage_path)

    first_result = service.run_demo(reset=True)
    second_result = service.run_demo(reset=True)

    assert first_result.processed_event_count == second_result.processed_event_count
    assert len(service.list_open_high_priority_tickets()) == second_result.high_priority_count
