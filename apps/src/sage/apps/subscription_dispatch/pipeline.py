from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ContentPublishSource,
    DispatchSink,
    PersonalizationFilter,
    SubscriptionMatcher,
)


def run_subscription_dispatch_pipeline(
    input_file: str, output_file: str, subscription_file: str | None = None
) -> None:
    env = LocalEnvironment("subscription_dispatch")
    (
        env.from_batch(ContentPublishSource, input_file=input_file)
        .map(SubscriptionMatcher, subscription_file=subscription_file)
        .map(PersonalizationFilter)
        .sink(DispatchSink, output_file=output_file)
    )
    env.submit(autostop=True)
