"""Explicit in-memory state store for the ticket triage MVP."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import (
    HistoricalResolution,
    KnowledgeBaseArticle,
    SimilarCaseMatch,
    TeamQueueSummary,
    TicketStatusSnapshot,
    TicketTriageResult,
)


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


class InMemoryTicketTriageStateStore:
    """Pluggable in-memory state store with optional JSON persistence."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = None if storage_path is None else Path(storage_path)
        self.knowledge_articles: dict[str, KnowledgeBaseArticle] = {}
        self.historical_resolutions: dict[str, HistoricalResolution] = {}
        self.tickets: dict[str, TicketStatusSnapshot] = {}
        self.triage_results: dict[str, TicketTriageResult] = {}

        if self.storage_path is not None and self.storage_path.exists():
            self._load()

    def has_reference_data(self) -> bool:
        return bool(self.knowledge_articles) and bool(self.historical_resolutions)

    def load_reference_data(
        self,
        knowledge_articles: list[KnowledgeBaseArticle],
        historical_resolutions: list[HistoricalResolution],
    ) -> None:
        self.knowledge_articles = {item.article_id: item for item in knowledge_articles}
        self.historical_resolutions = {item.case_id: item for item in historical_resolutions}
        self._persist()

    def reset(self) -> None:
        self.knowledge_articles = {}
        self.historical_resolutions = {}
        self.tickets = {}
        self.triage_results = {}
        self._persist()

    def save_ticket_snapshot(self, snapshot: TicketStatusSnapshot) -> None:
        self.tickets[snapshot.ticket_id] = snapshot
        self._persist()

    def get_ticket_snapshot(self, ticket_id: str) -> TicketStatusSnapshot | None:
        return self.tickets.get(ticket_id)

    def build_status_snapshot(self, ticket_id: str) -> TicketStatusSnapshot | None:
        return self.get_ticket_snapshot(ticket_id)

    def list_customer_recent_tickets(
        self,
        customer_id: str,
        limit: int | None = 5,
    ) -> list[TicketStatusSnapshot]:
        items = [item for item in self.tickets.values() if item.customer_id == customer_id]
        items.sort(key=lambda item: item.last_updated, reverse=True)
        return items if limit is None else items[:limit]

    def search_knowledge_articles(
        self,
        intent: str,
        normalized_text: str,
        limit: int | None = 3,
    ) -> list[SimilarCaseMatch]:
        matches: list[SimilarCaseMatch] = []
        for article in self.knowledge_articles.values():
            matched = [kw for kw in article.keywords if kw.lower() in normalized_text]
            base_score = 0.58 if article.intent == intent else 0.18 if matched else 0.0
            if base_score == 0.0:
                continue
            relevance_score = min(0.98, base_score + 0.1 * len(matched))
            matches.append(
                SimilarCaseMatch(
                    source_type="faq",
                    reference_id=article.article_id,
                    title=article.title,
                    relevance_score=round(relevance_score, 2),
                    suggested_team=article.assigned_team,
                    suggested_reply=article.answer_template,
                )
            )
        matches.sort(key=lambda item: item.relevance_score, reverse=True)
        return matches if limit is None else matches[:limit]

    def search_similar_resolutions(
        self,
        intent: str,
        normalized_text: str,
        limit: int | None = 3,
    ) -> list[SimilarCaseMatch]:
        matches: list[SimilarCaseMatch] = []
        for case in self.historical_resolutions.values():
            matched = [kw for kw in case.keywords if kw.lower() in normalized_text]
            base_score = 0.52 if case.intent == intent else 0.16 if matched else 0.0
            if base_score == 0.0:
                continue
            relevance_score = min(0.95, base_score + 0.08 * len(matched))
            matches.append(
                SimilarCaseMatch(
                    source_type="historical_case",
                    reference_id=case.case_id,
                    title=case.title,
                    relevance_score=round(relevance_score, 2),
                    suggested_team=case.assigned_team,
                    suggested_reply=case.resolution_template,
                )
            )
        matches.sort(key=lambda item: item.relevance_score, reverse=True)
        return matches if limit is None else matches[:limit]

    def append_triage_result(self, result: TicketTriageResult) -> None:
        self.triage_results[result.ticket_id] = result
        self._persist()

    def assign_team_queue(self, result: TicketTriageResult) -> None:
        self.triage_results[result.ticket_id] = result
        self._persist()

    def list_queue_summary(self) -> list[TeamQueueSummary]:
        queue_stats: dict[str, dict[str, int]] = {}
        for snapshot in self.tickets.values():
            team_stats = queue_stats.setdefault(
                snapshot.assigned_team,
                {
                    "open_ticket_count": 0,
                    "high_priority_count": 0,
                    "auto_reply_candidate_count": 0,
                },
            )
            team_stats["open_ticket_count"] += 1
            if snapshot.priority in {"high", "critical"}:
                team_stats["high_priority_count"] += 1
            if snapshot.auto_reply:
                team_stats["auto_reply_candidate_count"] += 1

        summaries = [
            TeamQueueSummary(
                team_name=team_name,
                open_ticket_count=stats["open_ticket_count"],
                high_priority_count=stats["high_priority_count"],
                auto_reply_candidate_count=stats["auto_reply_candidate_count"],
            )
            for team_name, stats in queue_stats.items()
        ]
        summaries.sort(
            key=lambda item: (item.high_priority_count, item.open_ticket_count, item.team_name),
            reverse=True,
        )
        return summaries

    def list_open_high_priority_tickets(self) -> list[TicketStatusSnapshot]:
        items = [item for item in self.tickets.values() if item.priority in {"high", "critical"}]
        items.sort(key=lambda item: (item.priority, item.last_updated), reverse=True)
        return items

    def list_triage_results(self) -> list[TicketTriageResult]:
        items = list(self.triage_results.values())
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def _persist(self) -> None:
        if self.storage_path is None:
            return

        if self.storage_path.parent and not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "knowledge_articles": [item.to_dict() for item in self.knowledge_articles.values()],
            "historical_resolutions": [
                item.to_dict() for item in self.historical_resolutions.values()
            ],
            "tickets": [item.to_dict() for item in self.tickets.values()],
            "triage_results": [item.to_dict() for item in self.triage_results.values()],
        }
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if self.storage_path is None:
            return

        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self.knowledge_articles = {
            item["article_id"]: KnowledgeBaseArticle.from_dict(item)
            for item in payload.get("knowledge_articles", [])
        }
        self.historical_resolutions = {
            item["case_id"]: HistoricalResolution.from_dict(item)
            for item in payload.get("historical_resolutions", [])
        }
        self.tickets = {
            item["ticket_id"]: TicketStatusSnapshot.from_dict(item)
            for item in payload.get("tickets", [])
        }
        self.triage_results = {
            item["ticket_id"]: TicketTriageResult.from_dict(item)
            for item in payload.get("triage_results", [])
        }
