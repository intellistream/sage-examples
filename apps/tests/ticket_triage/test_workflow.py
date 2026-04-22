from sage.apps.ticket_triage import TicketTriageApplicationService


def test_run_demo_generates_multiple_queues_and_priorities(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")

    result = service.run_demo(reset=True)

    intents = {item.intent for item in result.triage_results}
    queue_names = {item.team_name for item in result.queue_summaries}

    assert result.processed_event_count == 10
    assert result.high_priority_count >= 5
    assert "login_issue" in intents
    assert "refund_request" in intents
    assert "duty_manager" in queue_names
    assert "technical_support" in queue_names


def test_demo_creates_high_priority_ticket_snapshots(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")

    service.run_demo(reset=True)
    high_priority_tickets = service.list_open_high_priority_tickets()

    assert len(high_priority_tickets) >= 5
    assert all(item.priority in {"high", "critical"} for item in high_priority_tickets)
