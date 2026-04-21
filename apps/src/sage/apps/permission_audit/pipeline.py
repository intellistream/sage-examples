"""Permission audit pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    AuditLogParser,
    AuditLogSource,
    AuditRiskScorer,
    AuditSink,
    SensitiveActionDetector,
)


def run_permission_audit_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("permission_audit")
    (
        env.from_batch(AuditLogSource, input_file=input_file)
        .map(AuditLogParser)
        .map(SensitiveActionDetector)
        .map(AuditRiskScorer)
        .sink(AuditSink, output_file=output_file)
    )
    env.submit(autostop=True)
