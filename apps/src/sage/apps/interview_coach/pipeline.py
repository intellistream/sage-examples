from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import InterviewReportSink, InterviewAnswerSource, InterviewQuestionMapper, InterviewScorer, InterviewAdviceBuilder


def run_interview_coach_pipeline(answer_file: str, rubric_file: str, output_file: str) -> None:
    env = LocalEnvironment('interview_coach')
    (
        env.from_batch(InterviewAnswerSource, answer_file=answer_file, rubric_file=rubric_file)
        .map(InterviewQuestionMapper)
        .map(InterviewScorer)
        .map(InterviewAdviceBuilder)
        .sink(InterviewReportSink, output_file=output_file)
    )
    env.submit(autostop=True)
