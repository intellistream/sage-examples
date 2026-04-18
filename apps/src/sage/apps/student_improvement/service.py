"""Service facade and optional FastAPI adapter for the student improvement MVP."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from .demo_data import build_demo_curriculum, build_demo_exam_records
from .knowledge_base import CurriculumKnowledgeBase
from .models import Curriculum, ExamRecord
from .state_store import InMemoryStudentImprovementStateStore
from .workflow import StudentImprovementWorkflowRunner


def _to_payload(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_payload(item) for key, item in value.items()}
    return value


class StudentImprovementApplicationService:
    """High-level service interface for curriculum init, exam import, and queries."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.state_store = InMemoryStudentImprovementStateStore(storage_path=storage_path)
        self.workflow = StudentImprovementWorkflowRunner(self.state_store)

    def initialize_curriculum(self, curriculum: Curriculum | None = None):
        return self.workflow.initialize_curriculum(curriculum or build_demo_curriculum())

    def import_exam(self, exam: ExamRecord):
        return self.workflow.import_exam(exam)

    def get_student_diagnosis(self, student_id: str):
        diagnosis = self.state_store.get_latest_diagnosis(student_id)
        if diagnosis is None:
            raise KeyError(f"No diagnosis found for student '{student_id}'.")
        return diagnosis

    def get_wrong_question_bank(self, student_id: str):
        return self.state_store.get_wrong_questions(student_id)

    def get_student_profile(self, student_id: str):
        profile = self.state_store.get_profile(student_id)
        if profile is None:
            raise KeyError(f"No profile found for student '{student_id}'.")
        return profile

    def list_student_exams(self, student_id: str):
        return self.state_store.list_student_exams(student_id)

    def get_student_knowledge_graph(self, student_id: str | None = None):
        curriculum = self.state_store.get_curriculum()
        if curriculum is None:
            raise KeyError("Curriculum has not been initialized.")

        mastery_summary: dict[str, float] = {}
        resolved_student_id = student_id
        if student_id is not None:
            profile = self.state_store.get_profile(student_id)
            if profile is None:
                raise KeyError(f"No profile found for student '{student_id}'.")
            mastery_summary = dict(profile.mastery_summary)
        knowledge_base = CurriculumKnowledgeBase(curriculum)
        return knowledge_base.build_knowledge_graph(
            mastery_summary,
            student_id=resolved_student_id,
        )


def create_demo_application_service(
    storage_path: str | Path | None = None,
) -> StudentImprovementApplicationService:
    service = StudentImprovementApplicationService(storage_path=storage_path)
    service.initialize_curriculum(build_demo_curriculum())
    return service


def create_fastapi_app(
    service: StudentImprovementApplicationService | None = None,
) -> FastAPI:
    runtime_service = service or StudentImprovementApplicationService()
    app = FastAPI(title="SAGE Student Improvement MVP", version="0.1.0")

    @app.post("/curriculum/init")
    def initialize_curriculum(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        curriculum = build_demo_curriculum() if payload is None else Curriculum.from_dict(payload)
        result = runtime_service.initialize_curriculum(curriculum)
        return _to_payload(result)

    @app.post("/exams/import")
    def import_exam(payload: dict[str, Any]) -> dict[str, Any]:
        result = runtime_service.import_exam(ExamRecord.from_dict(payload))
        return _to_payload(result)

    @app.get("/students/{student_id}/diagnosis")
    def get_diagnosis(student_id: str) -> dict[str, Any]:
        try:
            return _to_payload(runtime_service.get_student_diagnosis(student_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/students/{student_id}/wrong-questions")
    def get_wrong_questions(student_id: str) -> list[dict[str, Any]]:
        return _to_payload(runtime_service.get_wrong_question_bank(student_id))

    @app.get("/students/{student_id}/profile")
    def get_profile(student_id: str) -> dict[str, Any]:
        try:
            return _to_payload(runtime_service.get_student_profile(student_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/students/{student_id}/knowledge-graph")
    def get_student_knowledge_graph(student_id: str) -> dict[str, Any]:
        try:
            return _to_payload(runtime_service.get_student_knowledge_graph(student_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/curriculum/knowledge-graph")
    def get_curriculum_knowledge_graph() -> dict[str, Any]:
        try:
            return _to_payload(runtime_service.get_student_knowledge_graph())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


def load_demo_exam_records() -> list[ExamRecord]:
    return build_demo_exam_records()
