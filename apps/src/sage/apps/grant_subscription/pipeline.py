from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import GrantAlertSink, GrantAnnouncementSource, GrantRuleExtractor, TeamProfileMatcher, GrantPriorityScorer


def run_grant_subscription_pipeline(announcement_file: str, profile_file: str, output_file: str) -> None:
    env = LocalEnvironment('grant_subscription')
    (
        env.from_batch(GrantAnnouncementSource, announcement_file=announcement_file, profile_file=profile_file)
        .map(GrantRuleExtractor)
        .map(TeamProfileMatcher)
        .map(GrantPriorityScorer)
        .sink(GrantAlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
