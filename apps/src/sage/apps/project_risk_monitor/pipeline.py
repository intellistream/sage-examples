from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import ProjectLogSource, ProjectRiskScorer, ProjectRiskSink, RiskKeywordExtractor


def run_project_risk_monitor_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("project_risk_monitor")
    (
        env.from_batch(ProjectLogSource, input_file=input_file)
        .map(RiskKeywordExtractor)
        .map(ProjectRiskScorer)
        .sink(ProjectRiskSink, output_file=output_file)
    )
    env.submit(autostop=True)
