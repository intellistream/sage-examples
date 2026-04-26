from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    LessonConflictChecker,
    LessonPlanScorer,
    LessonScheduleSink,
    TeachingConstraintParser,
    TeachingRequirementSource,
)


def run_lesson_scheduler_pipeline(plan_file: str, resource_file: str, output_file: str) -> None:
    env = LocalEnvironment("lesson_scheduler")
    (
        env.from_batch(TeachingRequirementSource, plan_file=plan_file, resource_file=resource_file)
        .map(TeachingConstraintParser)
        .map(LessonPlanScorer)
        .map(LessonConflictChecker)
        .sink(LessonScheduleSink, output_file=output_file)
    )
    env.submit(autostop=True)
