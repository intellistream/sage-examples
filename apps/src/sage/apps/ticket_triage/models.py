"""Structured models for the customer support ticket triage MVP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, TypeAlias


@dataclass(frozen=True)
class TicketEvent:
    ticket_id: str
    channel: str
    customer_id: str
    subject: str
    message: str
    created_at: str
    attachments: list[str] = field(default_factory=list)
    language: str = "zh"
    customer_tier: str = "standard"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TicketEvent:
        return cls(
            ticket_id=str(data["ticket_id"]),
            channel=str(data.get("channel", "email")),
            customer_id=str(data["customer_id"]),
            subject=str(data.get("subject", "")),
            message=str(data.get("message", "")),
            created_at=str(data["created_at"]),
            attachments=[str(item) for item in data.get("attachments", [])],
            language=str(data.get("language", "zh")),
            customer_tier=str(data.get("customer_tier", "standard")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TicketPayload: TypeAlias = TicketEvent | dict[str, Any]


def coerce_ticket_event(data: TicketPayload) -> TicketEvent:
    if isinstance(data, TicketEvent):
        return data
    return TicketEvent.from_dict(data)


@dataclass(frozen=True)
class KnowledgeBaseArticle:
    article_id: str
    title: str
    intent: str
    keywords: list[str]
    answer_template: str
    assigned_team: str = "l1_support"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeBaseArticle:
        return cls(
            article_id=str(data["article_id"]),
            title=str(data["title"]),
            intent=str(data["intent"]),
            keywords=[str(item) for item in data.get("keywords", [])],
            answer_template=str(data["answer_template"]),
            assigned_team=str(data.get("assigned_team", "l1_support")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalResolution:
    case_id: str
    title: str
    intent: str
    keywords: list[str]
    resolution_template: str
    assigned_team: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoricalResolution:
        return cls(
            case_id=str(data["case_id"]),
            title=str(data["title"]),
            intent=str(data["intent"]),
            keywords=[str(item) for item in data.get("keywords", [])],
            resolution_template=str(data["resolution_template"]),
            assigned_team=str(data["assigned_team"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedTicket:
    ticket_id: str
    channel: str
    customer_id: str
    subject: str
    message: str
    created_at: str
    language: str
    customer_tier: str
    attachments: list[str]
    normalized_text: str

    @classmethod
    def from_ticket(cls, ticket: TicketEvent, normalized_text: str) -> NormalizedTicket:
        return cls(
            ticket_id=ticket.ticket_id,
            channel=ticket.channel,
            customer_id=ticket.customer_id,
            subject=ticket.subject,
            message=ticket.message,
            created_at=ticket.created_at,
            language=ticket.language,
            customer_tier=ticket.customer_tier,
            attachments=list(ticket.attachments),
            normalized_text=normalized_text,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntentClassification:
    intent: str
    confidence: float
    matched_keywords: list[str]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UrgencyScore:
    score: int
    priority: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimilarCaseMatch:
    source_type: str
    reference_id: str
    title: str
    relevance_score: float
    suggested_team: str | None = None
    suggested_reply: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingDecision:
    assigned_team: str
    action: str
    auto_reply: bool
    escalation_required: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplyDraft:
    subject: str
    body: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TicketTriageResult:
    ticket_id: str
    intent: str
    priority: str
    urgency_score: int
    assigned_team: str
    recommended_action: str
    auto_reply: bool
    reply_draft: str
    reason_trace: list[str]
    matched_reference_ids: list[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TicketTriageResult:
        return cls(
            ticket_id=str(data["ticket_id"]),
            intent=str(data["intent"]),
            priority=str(data["priority"]),
            urgency_score=int(data["urgency_score"]),
            assigned_team=str(data["assigned_team"]),
            recommended_action=str(data["recommended_action"]),
            auto_reply=bool(data.get("auto_reply", False)),
            reply_draft=str(data.get("reply_draft", "")),
            reason_trace=[str(item) for item in data.get("reason_trace", [])],
            matched_reference_ids=[str(item) for item in data.get("matched_reference_ids", [])],
            created_at=str(data["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TicketStatusSnapshot:
    ticket_id: str
    customer_id: str
    channel: str
    status: str
    intent: str
    priority: str
    assigned_team: str
    recommended_action: str
    auto_reply: bool
    last_updated: str
    reason_trace: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TicketStatusSnapshot:
        return cls(
            ticket_id=str(data["ticket_id"]),
            customer_id=str(data["customer_id"]),
            channel=str(data["channel"]),
            status=str(data["status"]),
            intent=str(data["intent"]),
            priority=str(data["priority"]),
            assigned_team=str(data["assigned_team"]),
            recommended_action=str(data["recommended_action"]),
            auto_reply=bool(data.get("auto_reply", False)),
            last_updated=str(data["last_updated"]),
            reason_trace=[str(item) for item in data.get("reason_trace", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TeamQueueSummary:
    team_name: str
    open_ticket_count: int
    high_priority_count: int
    auto_reply_candidate_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TicketTriageRunResult:
    processed_event_count: int
    high_priority_count: int
    triage_results: list[TicketTriageResult]
    queue_summaries: list[TeamQueueSummary]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
