from sage.apps.ticket_triage import TicketEvent, TicketTriageApplicationService


def test_invoice_question_prefers_billing_and_auto_reply(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")

    result = service.ingest_tickets(
        [
            TicketEvent(
                ticket_id="T-INVOICE-1",
                channel="email",
                customer_id="CUST-X1",
                subject="电子发票怎么下载",
                message="我需要下载电子发票做报销，请给我入口。",
                created_at="2026-04-20T10:00:00",
            )
        ]
    )
    triage = result.triage_results[0]

    assert triage.intent == "invoice_issue"
    assert triage.assigned_team == "billing_ops"
    assert triage.auto_reply is True
    assert "发票" in triage.reply_draft


def test_repeat_login_issue_escalates_priority(tmp_path) -> None:
    service = TicketTriageApplicationService(storage_path=tmp_path / "ticket-state.json")

    result = service.ingest_tickets(
        [
            TicketEvent(
                ticket_id="T-LOGIN-1",
                channel="email",
                customer_id="CUST-X2",
                subject="无法登录",
                message="系统提示账号锁定。",
                created_at="2026-04-20T10:00:00",
            ),
            TicketEvent(
                ticket_id="T-LOGIN-2",
                channel="chat",
                customer_id="CUST-X2",
                subject="还是无法登录",
                message="我已经等待两天，账号锁定问题还没解决，请尽快处理。",
                created_at="2026-04-20T10:20:00",
                attachments=["locked-account.png"],
            ),
        ]
    )
    follow_up = result.triage_results[-1]

    assert follow_up.intent == "complaint_escalation"
    assert follow_up.priority in {"high", "critical"}
    assert follow_up.assigned_team == "duty_manager"