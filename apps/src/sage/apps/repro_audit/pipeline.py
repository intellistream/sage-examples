from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    ReproAuditSink,
    ReproConsistencyChecker,
    ReproManifestSource,
    ReproMetadataExtractor,
    ReproRiskScorer,
)


def run_repro_audit_pipeline(manifest_file: str, output_dir: str) -> None:
    env = LocalEnvironment('repro_audit')
    (
        env.from_batch(ReproManifestSource, manifest_file=manifest_file)
        .map(ReproMetadataExtractor)
        .map(ReproConsistencyChecker)
        .map(ReproRiskScorer)
        .sink(ReproAuditSink, output_dir=output_dir)
    )
    env.submit(autostop=True)
