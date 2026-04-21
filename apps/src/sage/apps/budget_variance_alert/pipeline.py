from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    BudgetAlertSink,
    BudgetCategoryMapper,
    BudgetPlanSource,
    BudgetVarianceDetector,
)


def run_budget_variance_alert_pipeline(plan_file: str, actual_file: str, output_file: str) -> None:
    env = LocalEnvironment("budget_variance_alert")
    (
        env.from_batch(BudgetPlanSource, plan_file=plan_file, actual_file=actual_file)
        .map(BudgetCategoryMapper)
        .map(BudgetVarianceDetector)
        .sink(BudgetAlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
