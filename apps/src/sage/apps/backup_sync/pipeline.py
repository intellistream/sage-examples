from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    BackupDispatcher,
    BackupReportSink,
    BackupSource,
    ConsistencyChecker,
    IncrementDetector,
)


def run_backup_sync_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("backup_sync")
    (
        env.from_batch(BackupSource, input_file=input_file)
        .map(IncrementDetector)
        .map(BackupDispatcher)
        .map(ConsistencyChecker)
        .sink(BackupReportSink, output_file=output_file)
    )
    env.submit(autostop=True)
