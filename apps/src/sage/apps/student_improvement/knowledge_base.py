"""Curriculum loading and question-to-knowledge-point resolution."""

from __future__ import annotations

from dataclasses import replace

from .models import (
    Curriculum,
    ExamQuestionResult,
    ExamRecord,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphSnapshot,
    KnowledgePoint,
    QuestionTemplate,
)


class CurriculumKnowledgeBase:
    """In-memory curriculum knowledge base for the MVP."""

    def __init__(self, curriculum: Curriculum) -> None:
        self.curriculum = curriculum
        self._chapter_index = {chapter.chapter_id: chapter for chapter in curriculum.chapters}
        self._knowledge_index = {
            knowledge.knowledge_point_id: knowledge for knowledge in curriculum.knowledge_points
        }
        self._question_index = {question.question_id: question for question in curriculum.question_bank}
        self._question_map = {
            key: list(value) for key, value in curriculum.question_to_knowledge_map.items()
        }

    def summarize(self) -> dict[str, int | str]:
        return {
            "curriculum_id": self.curriculum.curriculum_id,
            "chapter_count": len(self.curriculum.chapters),
            "knowledge_point_count": len(self.curriculum.knowledge_points),
            "question_count": len(self.curriculum.question_bank),
        }

    @staticmethod
    def mastery_status_from_score(mastery_score: float | None) -> str:
        if mastery_score is None:
            return "unknown"
        if mastery_score >= 0.8:
            return "mastered"
        if mastery_score >= 0.6:
            return "reviewing"
        return "unmastered"

    def get_question_template(self, question_id: str) -> QuestionTemplate | None:
        return self._question_index.get(question_id)

    def get_knowledge_point(self, knowledge_point_id: str) -> KnowledgePoint | None:
        return self._knowledge_index.get(knowledge_point_id)

    def describe_knowledge_points(self, knowledge_point_ids: list[str]) -> list[str]:
        names: list[str] = []
        for knowledge_point_id in knowledge_point_ids:
            knowledge_point = self.get_knowledge_point(knowledge_point_id)
            if knowledge_point is not None:
                names.append(knowledge_point.name)
        return names

    def get_prerequisite_chain(self, knowledge_point_id: str) -> list[str]:
        ordered: list[str] = []
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            node = self.get_knowledge_point(node_id)
            if node is None:
                return
            for parent_id in node.prerequisites:
                visit(parent_id)
                if parent_id not in ordered:
                    ordered.append(parent_id)

        visit(knowledge_point_id)
        return ordered

    def resolve_knowledge_points(self, question: ExamQuestionResult) -> list[str]:
        if question.knowledge_point_ids:
            return list(question.knowledge_point_ids)

        if question.question_id in self._question_map:
            return list(self._question_map[question.question_id])

        template = self.get_question_template(question.question_id)
        if template is not None:
            return list(template.knowledge_point_ids)

        prompt_text = question.prompt.lower()
        matched: list[str] = []
        for knowledge_point in self.curriculum.knowledge_points:
            aliases = [knowledge_point.name.lower(), knowledge_point.summary.lower()]
            aliases.extend(item.lower() for item in knowledge_point.practice_focus)
            if any(alias and alias.split()[0] in prompt_text for alias in aliases):
                matched.append(knowledge_point.knowledge_point_id)

        if matched:
            return matched

        raise ValueError(
            f"Unable to resolve knowledge points for question '{question.question_id}'. "
            "Provide explicit knowledge_point_ids or add the question to the curriculum.",
        )

    def resolve_solution_steps(self, question: ExamQuestionResult) -> list[str]:
        if question.solution_steps:
            return list(question.solution_steps)

        template = self.get_question_template(question.question_id)
        if template is not None and template.solution_steps:
            return list(template.solution_steps)

        knowledge_points = self.describe_knowledge_points(self.resolve_knowledge_points(question))
        return [
            f"先定位该题涉及的知识点：{', '.join(knowledge_points) or '基础运算'}。",
            "对照题目条件逐步列式或代入，避免跳步。",
            f"最后核对标准答案 {question.correct_answer}。",
        ]

    def enrich_question(self, question: ExamQuestionResult) -> ExamQuestionResult:
        template = self.get_question_template(question.question_id)
        return replace(
            question,
            prompt=template.prompt if template is not None and not question.prompt else question.prompt,
            correct_answer=(
                template.correct_answer
                if template is not None and not question.correct_answer
                else question.correct_answer
            ),
            knowledge_point_ids=self.resolve_knowledge_points(question),
            solution_steps=self.resolve_solution_steps(question),
            question_type=(
                template.question_type
                if template is not None and not question.question_type
                else question.question_type
            ),
        )

    def enrich_exam_record(self, exam: ExamRecord) -> ExamRecord:
        return replace(
            exam,
            questions=[self.enrich_question(question) for question in exam.questions],
        )

    def build_knowledge_graph(
        self,
        mastery_summary: dict[str, float] | None = None,
        *,
        student_id: str | None = None,
    ) -> KnowledgeGraphSnapshot:
        mastery_summary = mastery_summary or {}
        nodes: list[KnowledgeGraphNode] = []
        edges: list[KnowledgeGraphEdge] = []

        for chapter in self.curriculum.chapters:
            nodes.append(
                KnowledgeGraphNode(
                    node_id=chapter.chapter_id,
                    node_type="chapter",
                    label=chapter.title,
                    summary=chapter.summary,
                )
            )

        for knowledge_point in self.curriculum.knowledge_points:
            mastery_score = mastery_summary.get(knowledge_point.knowledge_point_id)
            nodes.append(
                KnowledgeGraphNode(
                    node_id=knowledge_point.knowledge_point_id,
                    node_type="knowledge_point",
                    label=knowledge_point.name,
                    summary=knowledge_point.summary,
                    chapter_id=knowledge_point.chapter_id,
                    mastery_score=mastery_score,
                    mastery_status=self.mastery_status_from_score(mastery_score),
                    prerequisite_ids=list(knowledge_point.prerequisites),
                )
            )
            edges.append(
                KnowledgeGraphEdge(
                    source_id=knowledge_point.chapter_id,
                    target_id=knowledge_point.knowledge_point_id,
                    relation="contains",
                )
            )
            for prerequisite_id in knowledge_point.prerequisites:
                edges.append(
                    KnowledgeGraphEdge(
                        source_id=prerequisite_id,
                        target_id=knowledge_point.knowledge_point_id,
                        relation="prerequisite_of",
                    )
                )

        return KnowledgeGraphSnapshot(
            curriculum_id=self.curriculum.curriculum_id,
            student_id=student_id,
            grade=self.curriculum.grade,
            subject=self.curriculum.subject,
            nodes=nodes,
            edges=edges,
        )
