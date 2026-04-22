from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import RepairScheduleSink, RepairTicketSource, RepairGeoMapper, RepairPriorityScorer, RepairRoutePlanner


def run_urban_repair_scheduler_pipeline(ticket_file: str, output_file: str) -> None:
    env = LocalEnvironment('urban_repair_scheduler')
    (
        env.from_batch(RepairTicketSource, ticket_file=ticket_file)
        .map(RepairGeoMapper)
        .map(RepairPriorityScorer)
        .map(RepairRoutePlanner)
        .sink(RepairScheduleSink, output_file=output_file)
    )
    env.submit(autostop=True)
