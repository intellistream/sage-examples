from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    CourseAnswerFormatter,
    CourseAnswerSink,
    CourseChunker,
    CourseDocSource,
    CourseQuestionMatcher,
)


def run_course_qa_helper_pipeline(doc_dir: str, question_file: str, output_file: str) -> None:
    env = LocalEnvironment('course_qa_helper')
    (
        env.from_batch(CourseDocSource, doc_dir=doc_dir, question_file=question_file)
        .flatmap(CourseChunker)
        .map(CourseQuestionMatcher)
        .map(CourseAnswerFormatter)
        .sink(CourseAnswerSink, output_file=output_file)
    )
    env.submit(autostop=True)
