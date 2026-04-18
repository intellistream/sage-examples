"""Explicit state stores for curriculum, exams, wrong questions, and diagnoses."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    Curriculum,
    ExamRecord,
    LearningDiagnosis,
    StudentProfile,
    WrongQuestionItem,
)


class CurriculumRepository:
    def __init__(self) -> None:
        self._curriculum: Curriculum | None = None

    def set(self, curriculum: Curriculum) -> None:
        self._curriculum = curriculum

    def get(self) -> Curriculum | None:
        return self._curriculum

    def to_dict(self) -> dict | None:
        return None if self._curriculum is None else self._curriculum.to_dict()

    def load_dict(self, payload: dict | None) -> None:
        self._curriculum = None if payload is None else Curriculum.from_dict(payload)


class ExamHistoryRepository:
    def __init__(self) -> None:
        self._records: dict[str, list[ExamRecord]] = {}

    def append(self, record: ExamRecord) -> None:
        self._records.setdefault(record.student_id, []).append(record)
        self._records[record.student_id].sort(key=lambda item: item.submitted_at)

    def list_by_student(self, student_id: str) -> list[ExamRecord]:
        return list(self._records.get(student_id, []))

    def to_dict(self) -> dict[str, list[dict]]:
        return {
            student_id: [record.to_dict() for record in records]
            for student_id, records in self._records.items()
        }

    def load_dict(self, payload: dict[str, list[dict]] | None) -> None:
        self._records = {}
        for student_id, records in dict(payload or {}).items():
            self._records[student_id] = [ExamRecord.from_dict(item) for item in records]


class WrongQuestionRepository:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, WrongQuestionItem]] = {}

    def replace_for_student(self, student_id: str, items: list[WrongQuestionItem]) -> None:
        self._items[student_id] = {item.question_id: item for item in items}

    def list_by_student(self, student_id: str) -> list[WrongQuestionItem]:
        entries = list(self._items.get(student_id, {}).values())
        return sorted(entries, key=lambda item: item.priority, reverse=True)

    def to_dict(self) -> dict[str, list[dict]]:
        return {
            student_id: [item.to_dict() for item in items.values()]
            for student_id, items in self._items.items()
        }

    def load_dict(self, payload: dict[str, list[dict]] | None) -> None:
        self._items = {}
        for student_id, items in dict(payload or {}).items():
            self._items[student_id] = {
                item_data["question_id"]: WrongQuestionItem.from_dict(item_data)
                for item_data in items
            }


class StudentProfileRepository:
    def __init__(self) -> None:
        self._profiles: dict[str, StudentProfile] = {}

    def save(self, profile: StudentProfile) -> None:
        self._profiles[profile.student_id] = profile

    def get(self, student_id: str) -> StudentProfile | None:
        return self._profiles.get(student_id)

    def to_dict(self) -> dict[str, dict]:
        return {student_id: profile.to_dict() for student_id, profile in self._profiles.items()}

    def load_dict(self, payload: dict[str, dict] | None) -> None:
        self._profiles = {
            student_id: StudentProfile.from_dict(profile)
            for student_id, profile in dict(payload or {}).items()
        }


class DiagnosisRepository:
    def __init__(self) -> None:
        self._diagnoses: dict[str, LearningDiagnosis] = {}

    def save(self, diagnosis: LearningDiagnosis) -> None:
        self._diagnoses[diagnosis.student_id] = diagnosis

    def get_latest(self, student_id: str) -> LearningDiagnosis | None:
        return self._diagnoses.get(student_id)

    def to_dict(self) -> dict[str, dict]:
        return {
            student_id: diagnosis.to_dict() for student_id, diagnosis in self._diagnoses.items()
        }

    def load_dict(self, payload: dict[str, dict] | None) -> None:
        self._diagnoses = {
            student_id: LearningDiagnosis.from_dict(diagnosis)
            for student_id, diagnosis in dict(payload or {}).items()
        }


class InMemoryStudentImprovementStateStore:
    """Pluggable in-memory state store with optional JSON persistence."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = None if storage_path is None else Path(storage_path)
        self.curriculum_repo = CurriculumRepository()
        self.exam_repo = ExamHistoryRepository()
        self.wrong_question_repo = WrongQuestionRepository()
        self.profile_repo = StudentProfileRepository()
        self.diagnosis_repo = DiagnosisRepository()

        if self.storage_path is not None and self.storage_path.exists():
            self._load()

    def initialize_curriculum(self, curriculum: Curriculum) -> None:
        self.curriculum_repo.set(curriculum)
        self._persist()

    def get_curriculum(self) -> Curriculum | None:
        return self.curriculum_repo.get()

    def append_exam(self, exam: ExamRecord) -> None:
        self.exam_repo.append(exam)
        self._persist()

    def list_student_exams(self, student_id: str) -> list[ExamRecord]:
        return self.exam_repo.list_by_student(student_id)

    def replace_wrong_questions(self, student_id: str, items: list[WrongQuestionItem]) -> None:
        self.wrong_question_repo.replace_for_student(student_id, items)
        self._persist()

    def get_wrong_questions(self, student_id: str) -> list[WrongQuestionItem]:
        return self.wrong_question_repo.list_by_student(student_id)

    def save_profile(self, profile: StudentProfile) -> None:
        self.profile_repo.save(profile)
        self._persist()

    def get_profile(self, student_id: str) -> StudentProfile | None:
        return self.profile_repo.get(student_id)

    def save_diagnosis(self, diagnosis: LearningDiagnosis) -> None:
        self.diagnosis_repo.save(diagnosis)
        self._persist()

    def get_latest_diagnosis(self, student_id: str) -> LearningDiagnosis | None:
        return self.diagnosis_repo.get_latest(student_id)

    def _persist(self) -> None:
        if self.storage_path is None:
            return

        if self.storage_path.parent and not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "curriculum": self.curriculum_repo.to_dict(),
            "exams": self.exam_repo.to_dict(),
            "wrong_questions": self.wrong_question_repo.to_dict(),
            "profiles": self.profile_repo.to_dict(),
            "diagnoses": self.diagnosis_repo.to_dict(),
        }
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if self.storage_path is None:
            return

        raw_payload = self.storage_path.read_text(encoding="utf-8")
        payload = json.loads(raw_payload)
        self.curriculum_repo.load_dict(payload.get("curriculum"))
        self.exam_repo.load_dict(payload.get("exams"))
        self.wrong_question_repo.load_dict(payload.get("wrong_questions"))
        self.profile_repo.load_dict(payload.get("profiles"))
        self.diagnosis_repo.load_dict(payload.get("diagnoses"))
