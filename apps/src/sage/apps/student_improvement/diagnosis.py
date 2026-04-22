"""Rule-based diagnosis and study path generation for the MVP."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .knowledge_base import CurriculumKnowledgeBase
from .models import (
    ExamRecord,
    LearningDiagnosis,
    StudentProfile,
    StudyPlanStep,
    WrongQuestionItem,
)


def _safe_float(value: str) -> float | None:
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return None


def classify_wrong_cause(
    question_prompt: str, student_answer: str, correct_answer: str
) -> list[str]:
    answer = student_answer.strip()
    correct = correct_answer.strip()
    lowered_prompt = question_prompt.lower()

    if not answer or answer in {"不会", "不知道", "空白"}:
        return ["步骤缺失"]

    answer_num = _safe_float(answer.replace("x =", "").replace("=", ""))
    correct_num = _safe_float(correct.replace("x =", "").replace("=", ""))
    if answer_num is not None and correct_num is not None:
        if abs(answer_num - correct_num) <= 2:
            return ["计算错误"]
        return ["公式误用"]

    if "函数" in lowered_prompt and answer.lstrip("-").isdigit():
        return ["概念错误"]

    if (
        any(keyword in lowered_prompt for keyword in ["解方程", "化简", "展开"])
        and "=" not in answer
    ):
        return ["步骤缺失"]

    if len(answer) < max(1, len(correct) // 2):
        return ["审题错误"]

    return ["概念错误"]


def build_wrong_question_items(
    exam: ExamRecord,
    knowledge_base: CurriculumKnowledgeBase,
) -> list[WrongQuestionItem]:
    wrong_items: list[WrongQuestionItem] = []
    for question in exam.questions:
        if question.is_correct:
            continue
        wrong_items.append(
            WrongQuestionItem(
                question_id=question.question_id,
                student_id=exam.student_id,
                prompt=question.prompt,
                student_answer=question.student_answer,
                correct_answer=question.correct_answer,
                standard_solution=list(question.solution_steps),
                knowledge_point_ids=list(question.knowledge_point_ids),
                wrong_cause_tags=classify_wrong_cause(
                    question.prompt,
                    question.student_answer,
                    question.correct_answer,
                ),
                last_seen_at=exam.submitted_at,
                mastery_status="unmastered",
                occurrence_count=1,
                priority=1.0 + len(question.knowledge_point_ids) * 0.2,
                related_exam_ids=[exam.exam_id],
            )
        )
    return wrong_items


def estimate_mastery_scores(
    knowledge_base: CurriculumKnowledgeBase,
    exams: list[ExamRecord],
) -> dict[str, float]:
    mastery_scores = {
        knowledge_point.knowledge_point_id: 0.5
        for knowledge_point in knowledge_base.curriculum.knowledge_points
    }
    if not exams:
        return mastery_scores

    weighted_scores: dict[str, list[tuple[float, float]]] = {key: [] for key in mastery_scores}
    total_exams = len(exams)

    for index, exam in enumerate(sorted(exams, key=lambda item: item.submitted_at), start=1):
        recency_weight = 0.6 + 0.4 * (index / total_exams)
        for question in exam.questions:
            if not question.knowledge_point_ids:
                continue
            ratio = 0.0 if question.full_score <= 0 else question.score / question.full_score
            for knowledge_point_id in question.knowledge_point_ids:
                weighted_scores.setdefault(knowledge_point_id, []).append((ratio, recency_weight))

    for knowledge_point_id, attempts in weighted_scores.items():
        if not attempts:
            continue
        weighted_total = sum(score * weight for score, weight in attempts)
        weight_sum = sum(weight for _, weight in attempts)
        accuracy = 0.0 if weight_sum <= 0 else weighted_total / weight_sum
        mastery_scores[knowledge_point_id] = round(min(1.0, max(0.0, 0.2 + 0.8 * accuracy)), 3)

    return mastery_scores


def merge_wrong_question_bank(
    existing_items: list[WrongQuestionItem],
    new_items: list[WrongQuestionItem],
    mastery_scores: dict[str, float],
    latest_exam: ExamRecord,
) -> list[WrongQuestionItem]:
    merged = {item.question_id: replace(item) for item in existing_items}

    for item in new_items:
        if item.question_id in merged:
            current = merged[item.question_id]
            merged[item.question_id] = replace(
                current,
                student_answer=item.student_answer,
                correct_answer=item.correct_answer,
                standard_solution=list(item.standard_solution),
                wrong_cause_tags=sorted(set(current.wrong_cause_tags + item.wrong_cause_tags)),
                last_seen_at=item.last_seen_at,
                occurrence_count=current.occurrence_count + 1,
                priority=round(current.priority + 0.6, 2),
                related_exam_ids=list(
                    dict.fromkeys(current.related_exam_ids + item.related_exam_ids)
                ),
                mastery_status="unmastered",
            )
        else:
            merged[item.question_id] = item

    latest_wrong_ids = {item.question_id for item in new_items}
    for question_id, item in list(merged.items()):
        max_mastery = max(
            (mastery_scores.get(kp_id, 0.5) for kp_id in item.knowledge_point_ids), default=0.5
        )
        updated_priority = item.priority
        updated_status = item.mastery_status
        if question_id not in latest_wrong_ids:
            updated_priority = round(max(0.3, item.priority - 0.2), 2)
            if max_mastery >= 0.8:
                updated_status = "mastered"
            elif max_mastery >= 0.6:
                updated_status = "reviewing"
        else:
            updated_status = "unmastered"
            updated_priority = round(item.priority + 0.3, 2)

        merged[question_id] = replace(
            item, mastery_status=updated_status, priority=updated_priority
        )

    return sorted(merged.values(), key=lambda wrong_item: wrong_item.priority, reverse=True)


def build_risk_ranking(
    knowledge_base: CurriculumKnowledgeBase,
    mastery_scores: dict[str, float],
    wrong_questions: list[WrongQuestionItem],
) -> list[dict[str, object]]:
    latest_wrong_counter: dict[str, int] = {}
    for wrong_item in wrong_questions:
        for knowledge_point_id in wrong_item.knowledge_point_ids:
            latest_wrong_counter[knowledge_point_id] = (
                latest_wrong_counter.get(knowledge_point_id, 0) + 1
            )

    rows: list[dict[str, object]] = []
    for knowledge_point in knowledge_base.curriculum.knowledge_points:
        mastery = mastery_scores.get(knowledge_point.knowledge_point_id, 0.5)
        wrong_count = latest_wrong_counter.get(knowledge_point.knowledge_point_id, 0)
        risk_score = round((1.0 - mastery) * 0.7 + min(1.0, wrong_count / 3.0) * 0.3, 3)
        rows.append(
            {
                "knowledge_point_id": knowledge_point.knowledge_point_id,
                "knowledge_point": knowledge_point.name,
                "mastery": mastery,
                "recent_wrong_count": wrong_count,
                "risk_score": risk_score,
            }
        )

    return sorted(rows, key=lambda item: item["risk_score"], reverse=True)


def build_study_plan(
    knowledge_base: CurriculumKnowledgeBase,
    weak_knowledge_points: list[dict[str, object]],
    wrong_questions: list[WrongQuestionItem],
) -> list[StudyPlanStep]:
    plan: list[StudyPlanStep] = []
    selected_knowledge_point_ids = [
        str(item["knowledge_point_id"]) for item in weak_knowledge_points[:3]
    ]

    prerequisites: list[str] = []
    for knowledge_point_id in selected_knowledge_point_ids:
        for prerequisite_id in knowledge_base.get_prerequisite_chain(knowledge_point_id):
            if (
                prerequisite_id not in prerequisites
                and prerequisite_id not in selected_knowledge_point_ids
            ):
                prerequisites.append(prerequisite_id)

    if prerequisites:
        plan.append(
            StudyPlanStep(
                step_index=len(plan) + 1,
                title="先补前置基础",
                rationale="部分薄弱点依赖更基础的分式或方程能力，先补基础可降低后续错误率。",
                target_knowledge_points=prerequisites,
                recommended_actions=[
                    "回顾课本例题与定义，补齐公式和基本步骤。",
                    "每个前置点至少完成 3 道基础题并记录关键步骤。",
                ],
            )
        )

    if selected_knowledge_point_ids:
        names = knowledge_base.describe_knowledge_points(selected_knowledge_point_ids)
        plan.append(
            StudyPlanStep(
                step_index=len(plan) + 1,
                title="集中突破核心薄弱点",
                rationale=f"当前最需要优先处理的知识点是：{', '.join(names)}。",
                target_knowledge_points=selected_knowledge_point_ids,
                recommended_actions=[
                    "对每个薄弱点做 2 道例题复盘 + 2 道同类变式。",
                    "把标准解法写成自己的步骤模板，避免下次重复犯错。",
                ],
            )
        )

    if wrong_questions:
        plan.append(
            StudyPlanStep(
                step_index=len(plan) + 1,
                title="用动态错题集做针对复习",
                rationale="先解决重复出现或优先级最高的错题，再进入新题训练。",
                target_knowledge_points=list(
                    dict.fromkeys(
                        knowledge_point_id
                        for item in wrong_questions[:3]
                        for knowledge_point_id in item.knowledge_point_ids
                    )
                ),
                recommended_actions=[
                    "先重做优先级最高的 3 道错题，并写出每一步原因。",
                    "对仍未掌握的题目，补做同知识点 2 道变式题。",
                ],
            )
        )

    plan.append(
        StudyPlanStep(
            step_index=len(plan) + 1,
            title="进行一次小规模综合训练",
            rationale="通过混合题型验证是否真的掌握，而不是只会原题。",
            target_knowledge_points=selected_knowledge_point_ids,
            recommended_actions=[
                "完成一份 20 分钟的小练习，覆盖薄弱点和其前置点。",
                "训练后再次导入结果，观察掌握度和错题状态是否改善。",
            ],
        )
    )

    return plan[:5]


def build_learning_diagnosis(
    student_id: str,
    knowledge_base: CurriculumKnowledgeBase,
    mastery_scores: dict[str, float],
    wrong_questions: list[WrongQuestionItem],
    generated_at: str | None = None,
) -> LearningDiagnosis:
    generated_at = generated_at or datetime.utcnow().isoformat()
    risk_ranking = build_risk_ranking(knowledge_base, mastery_scores, wrong_questions)
    weak_knowledge_points = [item for item in risk_ranking if float(item["mastery"]) < 0.7][:5]
    study_plan = build_study_plan(knowledge_base, weak_knowledge_points, wrong_questions)
    next_practice_tasks = [
        f"围绕 {item['knowledge_point']} 做 2 道基础题 + 1 道综合题"
        for item in weak_knowledge_points[:3]
    ]
    notes = [
        "掌握度采用规则型加权估计，最近一次考试权重更高。",
        "错因标签由规则识别生成，后续可以替换为大模型增强分析。",
    ]
    return LearningDiagnosis(
        diagnosis_id=f"diagnosis-{student_id}-{generated_at}",
        student_id=student_id,
        generated_at=generated_at,
        weak_knowledge_points=weak_knowledge_points,
        mastery_summary=mastery_scores,
        risk_ranking=risk_ranking,
        study_plan=study_plan,
        next_practice_tasks=next_practice_tasks,
        wrong_question_refs=[item.question_id for item in wrong_questions],
        notes=notes,
    )


def build_student_profile(
    exam: ExamRecord,
    diagnosis: LearningDiagnosis,
    wrong_questions: list[WrongQuestionItem],
    knowledge_base: CurriculumKnowledgeBase,
) -> StudentProfile:
    top_weak_names = [str(item["knowledge_point"]) for item in diagnosis.weak_knowledge_points[:3]]
    overview = "当前最需要优先提升的知识点：" + (
        "、".join(top_weak_names) if top_weak_names else "暂无明显薄弱点"
    )
    return StudentProfile(
        student_id=exam.student_id,
        grade=exam.grade,
        subject=exam.subject,
        mastery_summary=diagnosis.mastery_summary,
        latest_diagnosis_id=diagnosis.diagnosis_id,
        wrong_question_ids=[item.question_id for item in wrong_questions],
        study_plan_summary=[step.title for step in diagnosis.study_plan],
        diagnosis_overview=overview,
    )
