from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import SkillGapSink, LearningRecordSource, SkillMapper, SkillGapDetector, PracticePathBuilder


def run_skill_gap_diagnosis_pipeline(record_dir: str, output_file: str) -> None:
    env = LocalEnvironment('skill_gap_diagnosis')
    (
        env.from_batch(LearningRecordSource, record_dir=record_dir)
        .map(SkillMapper)
        .map(SkillGapDetector)
        .map(PracticePathBuilder)
        .sink(SkillGapSink, output_file=output_file)
    )
    env.submit(autostop=True)
