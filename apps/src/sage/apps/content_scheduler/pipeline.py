from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CampaignPlanSource,
    ChannelRuleMapper,
    ContentScheduleSink,
    ScheduleConflictDetector,
    TopicAllocator,
)


def run_content_scheduler_pipeline(plan_file: str, channel_file: str, output_file: str) -> None:
    env = LocalEnvironment("content_scheduler")
    (
        env.from_batch(CampaignPlanSource, plan_file=plan_file, channel_file=channel_file)
        .map(ChannelRuleMapper)
        .map(TopicAllocator)
        .map(ScheduleConflictDetector)
        .sink(ContentScheduleSink, output_file=output_file)
    )
    env.submit(autostop=True)
