"""Customer support ticket triage MVP built on top of SAGE stateful workflows."""

from .demo_data import (
    build_demo_historical_resolutions,
    build_demo_knowledge_articles,
    build_demo_summary,
    build_demo_tickets,
)
from .models import (
    HistoricalResolution,
    KnowledgeBaseArticle,
    TeamQueueSummary,
    TicketEvent,
    TicketStatusSnapshot,
    TicketTriageResult,
    TicketTriageRunResult,
)
from .service import (
    TicketTriageApplicationService,
    create_demo_application_service,
    create_fastapi_app,
)

__all__ = [
    "HistoricalResolution",
    "KnowledgeBaseArticle",
    "TeamQueueSummary",
    "TicketEvent",
    "TicketStatusSnapshot",
    "TicketTriageApplicationService",
    "TicketTriageResult",
    "TicketTriageRunResult",
    "build_demo_historical_resolutions",
    "build_demo_knowledge_articles",
    "build_demo_summary",
    "build_demo_tickets",
    "create_demo_application_service",
    "create_fastapi_app",
]