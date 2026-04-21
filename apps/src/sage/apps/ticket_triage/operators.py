"""SAGE operators for the customer support ticket triage MVP."""

from __future__ import annotations

from typing import Any

from sage.foundation import BatchFunction, MapFunction, SinkFunction

from .models import (
    IntentClassification,
    NormalizedTicket,
    ReplyDraft,
    RoutingDecision,
    SimilarCaseMatch,
    TicketEvent,
    TicketStatusSnapshot,
    TicketTriageResult,
    UrgencyScore,
    coerce_ticket_event,
)


STATE_SERVICE_NAME = "ticket_triage_state"

INTENT_KEYWORDS: dict[str, list[str]] = {
    "login_issue": ["无法登录", "账号锁定", "登录失败", "密码错误"],
    "refund_request": ["退款", "重复扣费", "扣费", "支付失败"],
    "invoice_issue": ["发票", "电子发票", "报销"],
    "order_delay": ["物流", "延迟", "送达", "订单"],
    "technical_support": ["报错", "500", "失败", "截图"],
    "complaint_escalation": ["投诉", "升级", "立即处理", "等待两天", "催办"],
    "general_inquiry": ["套餐", "功能", "导出", "专业版"],
}


def _normalize_text(ticket: TicketEvent) -> str:
    return f"{ticket.subject} {ticket.message}".strip().lower()


def _priority_rank(priority: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(priority, 1)


class DemoTicketSource(BatchFunction):
    """BatchFunction source that emits supplied tickets one by one."""

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


class NormalizeTicketStep(MapFunction):
    def execute(self, data: TicketEvent | dict[str, Any]) -> dict[str, Any]:
        ticket = coerce_ticket_event(data)
        normalized_ticket = NormalizedTicket.from_ticket(ticket, normalized_text=_normalize_text(ticket))
        return {
            "ticket": ticket,
            "normalized_ticket": normalized_ticket,
            "reason_trace": [f"渠道={ticket.channel}", f"客户等级={ticket.customer_tier}"],
        }


class EnrichCustomerContextStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        ticket: TicketEvent = data["ticket"]
        recent_tickets = self.call_service(
            STATE_SERVICE_NAME,
            ticket.customer_id,
            method="list_customer_recent_tickets",
        )
        return {
            **data,
            "recent_tickets": recent_tickets,
        }


class ClassifyIntentStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized_ticket: NormalizedTicket = data["normalized_ticket"]
        recent_tickets: list[TicketStatusSnapshot] = data["recent_tickets"]
        text = normalized_ticket.normalized_text

        complaint_keywords = [
            keyword
            for keyword in INTENT_KEYWORDS["complaint_escalation"]
            if keyword.lower() in text
        ]
        if complaint_keywords and recent_tickets:
            classification = IntentClassification(
                intent="complaint_escalation",
                confidence=0.9,
                matched_keywords=complaint_keywords,
                explanation=(
                    "命中升级类关键词，且该客户已有历史工单，按投诉升级优先处理。"
                ),
            )
            return {
                **data,
                "classification": classification,
            }

        best_intent = "general_inquiry"
        best_keywords: list[str] = []
        for intent, keywords in INTENT_KEYWORDS.items():
            matched = [keyword for keyword in keywords if keyword.lower() in text]
            if len(matched) > len(best_keywords):
                best_intent = intent
                best_keywords = matched

        confidence = 0.45 + min(0.45, 0.12 * len(best_keywords))
        if not best_keywords and best_intent == "general_inquiry":
            explanation = "未命中强规则，回退为通用咨询。"
        else:
            explanation = f"命中关键词: {', '.join(best_keywords)}"
        classification = IntentClassification(
            intent=best_intent,
            confidence=round(confidence, 2),
            matched_keywords=best_keywords,
            explanation=explanation,
        )
        return {
            **data,
            "classification": classification,
        }


class ScoreUrgencyStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        ticket: TicketEvent = data["ticket"]
        normalized_ticket: NormalizedTicket = data["normalized_ticket"]
        classification: IntentClassification = data["classification"]
        recent_tickets: list[TicketStatusSnapshot] = data["recent_tickets"]

        score = 25
        reasons = ["默认初始分=25"]
        text = normalized_ticket.normalized_text

        if classification.intent in {"login_issue", "technical_support"}:
            score += 20
            reasons.append("故障类问题，加 20 分")
        if classification.intent == "order_delay":
            score += 10
            reasons.append("履约延迟场景，加 10 分")
        if classification.intent in {"refund_request", "complaint_escalation"}:
            score += 25
            reasons.append("资金或投诉场景，加 25 分")
        if any(keyword in text for keyword in ["立即处理", "等待两天", "尽快", "催办"]):
            score += 20
            reasons.append("命中紧急关键词，加 20 分")
        if any(keyword in text for keyword in ["账号锁定", "扣费", "支付失败", "500", "投诉升级"]):
            score += 10
            reasons.append("命中高风险信号，加 10 分")
        if recent_tickets and any(item.intent == classification.intent for item in recent_tickets):
            score += 15
            reasons.append("同客户重复报障，加 15 分")
        if ticket.customer_tier in {"vip", "enterprise"}:
            score += 10
            reasons.append("高价值客户，加 10 分")
        if ticket.attachments:
            score += 10
            reasons.append("带附件需人工复核，加 10 分")
        if ticket.channel == "chat":
            score += 5
            reasons.append("在线聊天要求即时响应，加 5 分")

        if score >= 85:
            priority = "critical"
        elif score >= 65:
            priority = "high"
        elif score >= 45:
            priority = "medium"
        else:
            priority = "low"

        urgency = UrgencyScore(score=score, priority=priority, reasons=reasons)
        return {
            **data,
            "urgency": urgency,
        }


class RecallSimilarCasesStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized_ticket: NormalizedTicket = data["normalized_ticket"]
        classification: IntentClassification = data["classification"]

        knowledge_matches = self.call_service(
            STATE_SERVICE_NAME,
            classification.intent,
            normalized_ticket.normalized_text,
            method="search_knowledge_articles",
        )
        historical_matches = self.call_service(
            STATE_SERVICE_NAME,
            classification.intent,
            normalized_ticket.normalized_text,
            method="search_similar_resolutions",
        )
        combined_matches = sorted(
            [*knowledge_matches, *historical_matches],
            key=lambda item: item.relevance_score,
            reverse=True,
        )
        return {
            **data,
            "knowledge_matches": knowledge_matches,
            "historical_matches": historical_matches,
            "combined_matches": combined_matches,
        }


class DecideRouteStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        classification: IntentClassification = data["classification"]
        urgency: UrgencyScore = data["urgency"]
        knowledge_matches: list[SimilarCaseMatch] = data["knowledge_matches"]

        assigned_team = "l1_support"
        action = "manual_triage"
        escalation_required = False

        if classification.intent == "complaint_escalation" or urgency.priority == "critical":
            assigned_team = "duty_manager"
            action = "supervisor_escalation"
            escalation_required = True
        elif classification.intent in {"refund_request", "invoice_issue"}:
            assigned_team = "billing_ops"
            action = "billing_review"
        elif classification.intent == "order_delay":
            assigned_team = "order_ops"
            action = "order_follow_up"
        elif classification.intent in {"login_issue", "technical_support"}:
            assigned_team = "technical_support"
            action = "technical_triage"

        auto_reply = bool(
            knowledge_matches
            and knowledge_matches[0].relevance_score >= 0.7
            and urgency.priority in {"low", "medium"}
            and not escalation_required
        )
        if auto_reply:
            action = "send_auto_reply"
            reason = "命中高相关 FAQ 且优先级不高，先自动回复。"
        elif escalation_required:
            reason = "工单涉及投诉升级或紧急度极高，直接转主管队列。"
        else:
            reason = f"根据意图 {classification.intent} 和优先级 {urgency.priority} 路由到 {assigned_team}。"

        routing = RoutingDecision(
            assigned_team=assigned_team,
            action=action,
            auto_reply=auto_reply,
            escalation_required=escalation_required,
            reason=reason,
        )
        return {
            **data,
            "routing": routing,
        }


class DraftReplyStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        ticket: TicketEvent = data["ticket"]
        routing: RoutingDecision = data["routing"]
        matches: list[SimilarCaseMatch] = data["combined_matches"]

        if routing.auto_reply and matches:
            top_match = matches[0]
            reply = ReplyDraft(
                subject=f"关于工单 {ticket.ticket_id} 的处理建议",
                body=top_match.suggested_reply or "您好，我们已收到您的问题并正在处理。",
                source=top_match.source_type,
            )
        else:
            reply = ReplyDraft(
                subject="",
                body="",
                source="manual",
            )
        return {
            **data,
            "reply": reply,
        }


class PersistTicketStateStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> TicketTriageResult:
        ticket: TicketEvent = data["ticket"]
        classification: IntentClassification = data["classification"]
        urgency: UrgencyScore = data["urgency"]
        routing: RoutingDecision = data["routing"]
        reply: ReplyDraft = data["reply"]
        matches: list[SimilarCaseMatch] = data["combined_matches"]

        reason_trace = list(data["reason_trace"])
        reason_trace.append(classification.explanation)
        reason_trace.extend(urgency.reasons)
        reason_trace.append(routing.reason)

        result = TicketTriageResult(
            ticket_id=ticket.ticket_id,
            intent=classification.intent,
            priority=urgency.priority,
            urgency_score=urgency.score,
            assigned_team=routing.assigned_team,
            recommended_action=routing.action,
            auto_reply=routing.auto_reply,
            reply_draft=reply.body,
            reason_trace=reason_trace,
            matched_reference_ids=[item.reference_id for item in matches[:3]],
            created_at=ticket.created_at,
        )
        snapshot = TicketStatusSnapshot(
            ticket_id=ticket.ticket_id,
            customer_id=ticket.customer_id,
            channel=ticket.channel,
            status="open",
            intent=classification.intent,
            priority=urgency.priority,
            assigned_team=routing.assigned_team,
            recommended_action=routing.action,
            auto_reply=routing.auto_reply,
            last_updated=ticket.created_at,
            reason_trace=reason_trace,
        )
        self.call_service(STATE_SERVICE_NAME, snapshot, method="save_ticket_snapshot")
        self.call_service(STATE_SERVICE_NAME, result, method="append_triage_result")
        self.call_service(STATE_SERVICE_NAME, result, method="assign_team_queue")
        return result


class ResultCollectorSink(SinkFunction):
    def __init__(self, results: list[TicketTriageResult], **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results

    def execute(self, data: TicketTriageResult) -> None:
        self.results.append(data)