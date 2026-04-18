"""Structured models for the student improvement MVP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chapter:
    chapter_id: str
    title: str
    summary: str
    knowledge_point_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chapter:
        return cls(
            chapter_id=str(data["chapter_id"]),
            title=str(data["title"]),
            summary=str(data.get("summary", "")),
            knowledge_point_ids=list(data.get("knowledge_point_ids", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgePoint:
    knowledge_point_id: str
    name: str
    chapter_id: str
    summary: str
    prerequisites: list[str] = field(default_factory=list)
    practice_focus: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgePoint:
        return cls(
            knowledge_point_id=str(data["knowledge_point_id"]),
            name=str(data["name"]),
            chapter_id=str(data["chapter_id"]),
            summary=str(data.get("summary", "")),
            prerequisites=list(data.get("prerequisites", [])),
            practice_focus=list(data.get("practice_focus", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QuestionTemplate:
    question_id: str
    prompt: str
    correct_answer: str
    solution_steps: list[str]
    knowledge_point_ids: list[str]
    question_type: str = "short_answer"
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuestionTemplate:
        return cls(
            question_id=str(data["question_id"]),
            prompt=str(data["prompt"]),
            correct_answer=str(data["correct_answer"]),
            solution_steps=list(data.get("solution_steps", [])),
            knowledge_point_ids=list(data.get("knowledge_point_ids", [])),
            question_type=str(data.get("question_type", "short_answer")),
            tags=list(data.get("tags", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Curriculum:
    curriculum_id: str
    grade: str
    subject: str
    chapters: list[Chapter]
    knowledge_points: list[KnowledgePoint]
    question_bank: list[QuestionTemplate]
    question_to_knowledge_map: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Curriculum:
        return cls(
            curriculum_id=str(data["curriculum_id"]),
            grade=str(data["grade"]),
            subject=str(data["subject"]),
            chapters=[Chapter.from_dict(item) for item in data.get("chapters", [])],
            knowledge_points=[
                KnowledgePoint.from_dict(item) for item in data.get("knowledge_points", [])
            ],
            question_bank=[
                QuestionTemplate.from_dict(item) for item in data.get("question_bank", [])
            ],
            question_to_knowledge_map={
                str(key): list(value)
                for key, value in dict(data.get("question_to_knowledge_map", {})).items()
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExamQuestionResult:
    question_id: str
    prompt: str
    student_answer: str
    correct_answer: str
    score: float
    full_score: float
    knowledge_point_ids: list[str] = field(default_factory=list)
    solution_steps: list[str] = field(default_factory=list)
    question_type: str = "short_answer"

    @property
    def is_correct(self) -> bool:
        return self.score >= self.full_score

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExamQuestionResult:
        return cls(
            question_id=str(data["question_id"]),
            prompt=str(data["prompt"]),
            student_answer=str(data.get("student_answer", "")),
            correct_answer=str(data.get("correct_answer", "")),
            score=float(data.get("score", 0.0)),
            full_score=float(data.get("full_score", 0.0)),
            knowledge_point_ids=list(data.get("knowledge_point_ids", [])),
            solution_steps=list(data.get("solution_steps", [])),
            question_type=str(data.get("question_type", "short_answer")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExamRecord:
    exam_id: str
    student_id: str
    grade: str
    subject: str
    submitted_at: str
    questions: list[ExamQuestionResult]
    total_score: float
    max_score: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExamRecord:
        return cls(
            exam_id=str(data["exam_id"]),
            student_id=str(data["student_id"]),
            grade=str(data["grade"]),
            subject=str(data["subject"]),
            submitted_at=str(data["submitted_at"]),
            questions=[ExamQuestionResult.from_dict(item) for item in data.get("questions", [])],
            total_score=float(data.get("total_score", 0.0)),
            max_score=float(data.get("max_score", 0.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WrongQuestionItem:
    question_id: str
    student_id: str
    prompt: str
    student_answer: str
    correct_answer: str
    standard_solution: list[str]
    knowledge_point_ids: list[str]
    wrong_cause_tags: list[str]
    last_seen_at: str
    mastery_status: str = "unmastered"
    occurrence_count: int = 1
    priority: float = 1.0
    related_exam_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WrongQuestionItem:
        return cls(
            question_id=str(data["question_id"]),
            student_id=str(data["student_id"]),
            prompt=str(data["prompt"]),
            student_answer=str(data.get("student_answer", "")),
            correct_answer=str(data.get("correct_answer", "")),
            standard_solution=list(data.get("standard_solution", [])),
            knowledge_point_ids=list(data.get("knowledge_point_ids", [])),
            wrong_cause_tags=list(data.get("wrong_cause_tags", [])),
            last_seen_at=str(data["last_seen_at"]),
            mastery_status=str(data.get("mastery_status", "unmastered")),
            occurrence_count=int(data.get("occurrence_count", 1)),
            priority=float(data.get("priority", 1.0)),
            related_exam_ids=list(data.get("related_exam_ids", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StudyPlanStep:
    step_index: int
    title: str
    rationale: str
    target_knowledge_points: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StudyPlanStep:
        return cls(
            step_index=int(data["step_index"]),
            title=str(data["title"]),
            rationale=str(data.get("rationale", "")),
            target_knowledge_points=list(data.get("target_knowledge_points", [])),
            recommended_actions=list(data.get("recommended_actions", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningDiagnosis:
    diagnosis_id: str
    student_id: str
    generated_at: str
    weak_knowledge_points: list[dict[str, Any]] = field(default_factory=list)
    mastery_summary: dict[str, float] = field(default_factory=dict)
    risk_ranking: list[dict[str, Any]] = field(default_factory=list)
    study_plan: list[StudyPlanStep] = field(default_factory=list)
    next_practice_tasks: list[str] = field(default_factory=list)
    wrong_question_refs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningDiagnosis:
        return cls(
            diagnosis_id=str(data["diagnosis_id"]),
            student_id=str(data["student_id"]),
            generated_at=str(data["generated_at"]),
            weak_knowledge_points=list(data.get("weak_knowledge_points", [])),
            mastery_summary={
                str(key): float(value)
                for key, value in dict(data.get("mastery_summary", {})).items()
            },
            risk_ranking=list(data.get("risk_ranking", [])),
            study_plan=[StudyPlanStep.from_dict(item) for item in data.get("study_plan", [])],
            next_practice_tasks=list(data.get("next_practice_tasks", [])),
            wrong_question_refs=list(data.get("wrong_question_refs", [])),
            notes=list(data.get("notes", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["study_plan"] = [step.to_dict() for step in self.study_plan]
        return payload


@dataclass(frozen=True)
class KnowledgeGraphNode:
    node_id: str
    node_type: str
    label: str
    summary: str
    chapter_id: str | None = None
    mastery_score: float | None = None
    mastery_status: str = "unknown"
    prerequisite_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraphNode:
        mastery_score = data.get("mastery_score")
        return cls(
            node_id=str(data["node_id"]),
            node_type=str(data["node_type"]),
            label=str(data["label"]),
            summary=str(data.get("summary", "")),
            chapter_id=data.get("chapter_id"),
            mastery_score=None if mastery_score is None else float(mastery_score),
            mastery_status=str(data.get("mastery_status", "unknown")),
            prerequisite_ids=list(data.get("prerequisite_ids", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeGraphEdge:
    source_id: str
    target_id: str
    relation: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraphEdge:
        return cls(
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            relation=str(data["relation"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeGraphSnapshot:
    curriculum_id: str
    student_id: str | None
    grade: str
    subject: str
    nodes: list[KnowledgeGraphNode]
    edges: list[KnowledgeGraphEdge]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraphSnapshot:
        return cls(
            curriculum_id=str(data["curriculum_id"]),
            student_id=data.get("student_id"),
            grade=str(data["grade"]),
            subject=str(data["subject"]),
            nodes=[KnowledgeGraphNode.from_dict(item) for item in data.get("nodes", [])],
            edges=[KnowledgeGraphEdge.from_dict(item) for item in data.get("edges", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "curriculum_id": self.curriculum_id,
            "student_id": self.student_id,
            "grade": self.grade,
            "subject": self.subject,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }


@dataclass
class StudentProfile:
    student_id: str
    grade: str
    subject: str
    mastery_summary: dict[str, float] = field(default_factory=dict)
    latest_diagnosis_id: str | None = None
    wrong_question_ids: list[str] = field(default_factory=list)
    study_plan_summary: list[str] = field(default_factory=list)
    diagnosis_overview: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StudentProfile:
        return cls(
            student_id=str(data["student_id"]),
            grade=str(data["grade"]),
            subject=str(data["subject"]),
            mastery_summary={
                str(key): float(value)
                for key, value in dict(data.get("mastery_summary", {})).items()
            },
            latest_diagnosis_id=data.get("latest_diagnosis_id"),
            wrong_question_ids=list(data.get("wrong_question_ids", [])),
            study_plan_summary=list(data.get("study_plan_summary", [])),
            diagnosis_overview=str(data.get("diagnosis_overview", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurriculumInitializationResult:
    curriculum_id: str
    chapter_count: int
    knowledge_point_count: int
    question_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExamImportResult:
    exam_id: str
    student_id: str
    total_score: float
    max_score: float
    wrong_question_count: int
    wrong_questions: list[WrongQuestionItem]
    diagnosis: LearningDiagnosis
    profile: StudentProfile

    def to_dict(self) -> dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "student_id": self.student_id,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "wrong_question_count": self.wrong_question_count,
            "wrong_questions": [item.to_dict() for item in self.wrong_questions],
            "diagnosis": self.diagnosis.to_dict(),
            "profile": self.profile.to_dict(),
        }
