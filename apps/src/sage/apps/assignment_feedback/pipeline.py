from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import AssignmentFeedbackSink, AssignmentDraftSource, AssignmentSectionParser, RubricMatcher, FeedbackComposer


def run_assignment_feedback_pipeline(draft_file: str, rubric_file: str, output_file: str) -> None:
    env = LocalEnvironment('assignment_feedback')
    (
        env.from_batch(AssignmentDraftSource, draft_file=draft_file, rubric_file=rubric_file)
        .map(AssignmentSectionParser)
        .map(RubricMatcher)
        .map(FeedbackComposer)
        .sink(AssignmentFeedbackSink, output_file=output_file)
    )
    env.submit(autostop=True)
