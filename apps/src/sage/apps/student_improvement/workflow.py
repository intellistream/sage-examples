"""SAGE workflow orchestration for the student improvement MVP."""

from __future__ import annotations

from typing import Any

from sage.foundation import MapFunction, SinkFunction
from sage.runtime import BaseService, LocalEnvironment

from .diagnosis import (
    build_learning_diagnosis,
    build_student_profile,
    build_wrong_question_items,
    estimate_mastery_scores,
    merge_wrong_question_bank,
)
from .knowledge_base import CurriculumKnowledgeBase
from .models import Curriculum, CurriculumInitializationResult, ExamImportResult, ExamRecord
from .state_store import InMemoryStudentImprovementStateStore

STATE_SERVICE_NAME = "student_improvement_state"


class StudentImprovementStateService(BaseService):
    """Runtime service exposing explicit state operations to workflow nodes."""

    def __init__(self, store: InMemoryStudentImprovementStateStore) -> None:
        super().__init__()
        self.store = store

    def initialize_curriculum(self, curriculum: Curriculum) -> CurriculumInitializationResult:
        self.store.initialize_curriculum(curriculum)
        knowledge_base = CurriculumKnowledgeBase(curriculum)
        summary = knowledge_base.summarize()
        return CurriculumInitializationResult(
            curriculum_id=str(summary["curriculum_id"]),
            chapter_count=int(summary["chapter_count"]),
            knowledge_point_count=int(summary["knowledge_point_count"]),
            question_count=int(summary["question_count"]),
        )

    def get_curriculum(self) -> Curriculum | None:
        return self.store.get_curriculum()

    def list_student_exams(self, student_id: str) -> list[ExamRecord]:
        return self.store.list_student_exams(student_id)

    def get_wrong_questions(self, student_id: str):
        return self.store.get_wrong_questions(student_id)

    def append_exam(self, exam: ExamRecord) -> None:
        self.store.append_exam(exam)

    def replace_wrong_questions(self, student_id: str, wrong_questions) -> None:
        self.store.replace_wrong_questions(student_id, wrong_questions)

    def save_diagnosis(self, diagnosis) -> None:
        self.store.save_diagnosis(diagnosis)

    def save_profile(self, profile) -> None:
        self.store.save_profile(profile)

    def get_latest_diagnosis(self, student_id: str):
        return self.store.get_latest_diagnosis(student_id)

    def get_profile(self, student_id: str):
        return self.store.get_profile(student_id)


class InitializeCurriculumStep(MapFunction):
    def execute(self, data: Curriculum | dict[str, Any]) -> CurriculumInitializationResult:
        curriculum = data if isinstance(data, Curriculum) else Curriculum.from_dict(data)
        return self.call_service(STATE_SERVICE_NAME, curriculum, method="initialize_curriculum")


class PrepareExamContextStep(MapFunction):
    def execute(self, data: ExamRecord | dict[str, Any]) -> dict[str, Any]:
        exam = data if isinstance(data, ExamRecord) else ExamRecord.from_dict(data)
        curriculum = self.call_service(STATE_SERVICE_NAME, method="get_curriculum")
        if curriculum is None:
            raise RuntimeError("Curriculum has not been initialized. Run initialize_curriculum first.")

        knowledge_base = CurriculumKnowledgeBase(curriculum)
        enriched_exam = knowledge_base.enrich_exam_record(exam)
        history = self.call_service(
            STATE_SERVICE_NAME,
            exam.student_id,
            method="list_student_exams",
        )
        existing_wrong_questions = self.call_service(
            STATE_SERVICE_NAME,
            exam.student_id,
            method="get_wrong_questions",
        )
        return {
            "curriculum": curriculum,
            "exam": enriched_exam,
            "history": history,
            "existing_wrong_questions": existing_wrong_questions,
        }


class DiagnoseExamStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        curriculum = data["curriculum"]
        exam = data["exam"]
        knowledge_base = CurriculumKnowledgeBase(curriculum)
        new_wrong_questions = build_wrong_question_items(exam, knowledge_base)
        return {
            **data,
            "new_wrong_questions": new_wrong_questions,
        }


class UpdateStudentStateStep(MapFunction):
    def execute(self, data: dict[str, Any]) -> ExamImportResult:
        curriculum = data["curriculum"]
        exam = data["exam"]
        history = list(data["history"])
        existing_wrong_questions = list(data["existing_wrong_questions"])
        new_wrong_questions = list(data["new_wrong_questions"])

        knowledge_base = CurriculumKnowledgeBase(curriculum)
        all_exams = history + [exam]
        mastery_scores = estimate_mastery_scores(knowledge_base, all_exams)
        merged_wrong_questions = merge_wrong_question_bank(
            existing_wrong_questions,
            new_wrong_questions,
            mastery_scores,
            exam,
        )
        diagnosis = build_learning_diagnosis(
            student_id=exam.student_id,
            knowledge_base=knowledge_base,
            mastery_scores=mastery_scores,
            wrong_questions=merged_wrong_questions,
            generated_at=exam.submitted_at,
        )
        profile = build_student_profile(exam, diagnosis, merged_wrong_questions, knowledge_base)

        self.call_service(STATE_SERVICE_NAME, exam, method="append_exam")
        self.call_service(
            STATE_SERVICE_NAME,
            exam.student_id,
            merged_wrong_questions,
            method="replace_wrong_questions",
        )
        self.call_service(STATE_SERVICE_NAME, diagnosis, method="save_diagnosis")
        self.call_service(STATE_SERVICE_NAME, profile, method="save_profile")

        return ExamImportResult(
            exam_id=exam.exam_id,
            student_id=exam.student_id,
            total_score=exam.total_score,
            max_score=exam.max_score,
            wrong_question_count=len(new_wrong_questions),
            wrong_questions=merged_wrong_questions,
            diagnosis=diagnosis,
            profile=profile,
        )


class ResultCollectorSink(SinkFunction):
    def __init__(self, results: list[Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results

    def execute(self, data: Any) -> None:
        self.results.append(data)


class StudentImprovementWorkflowRunner:
    """Thin workflow runner that rebuilds a LocalEnvironment per operation."""

    def __init__(self, state_store: InMemoryStudentImprovementStateStore | None = None) -> None:
        self.state_store = state_store or InMemoryStudentImprovementStateStore()

    def _build_environment(self, name: str) -> LocalEnvironment:
        environment = LocalEnvironment(name)
        environment.set_console_log_level("ERROR")
        environment.register_service(STATE_SERVICE_NAME, StudentImprovementStateService, self.state_store)
        return environment

    def initialize_curriculum(self, curriculum: Curriculum) -> CurriculumInitializationResult:
        results: list[CurriculumInitializationResult] = []
        environment = self._build_environment("student_improvement_init_curriculum")
        environment.from_batch([curriculum]).map(InitializeCurriculumStep).sink(
            ResultCollectorSink,
            results=results,
        )
        environment.submit(autostop=True)
        return results[-1]

    def import_exam(self, exam: ExamRecord) -> ExamImportResult:
        results: list[ExamImportResult] = []
        environment = self._build_environment("student_improvement_import_exam")
        (
            environment.from_batch([exam])
            .map(PrepareExamContextStep)
            .map(DiagnoseExamStep)
            .map(UpdateStudentStateStep)
            .sink(ResultCollectorSink, results=results)
        )
        environment.submit(autostop=True)
        return results[-1]
