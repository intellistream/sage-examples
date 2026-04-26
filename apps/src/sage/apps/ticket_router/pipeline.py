"""Ticket router pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    LoadBalancer,
    NotificationSink,
    PriorityScorer,
    TicketClassifier,
    TicketParser,
    TicketSource,
)


def run_ticket_router_pipeline(
    input_file: str, output_file: str, agents: list[str] | None = None
) -> None:
    env = LocalEnvironment("ticket_router")
    (
        env.from_batch(TicketSource, input_file=input_file)
        .map(TicketParser)
        .map(TicketClassifier)
        .map(PriorityScorer)
        .map(LoadBalancer, agents=agents)
        .sink(NotificationSink, output_file=output_file)
    )
    env.submit(autostop=True)
