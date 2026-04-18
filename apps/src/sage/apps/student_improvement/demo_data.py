"""Demo curriculum and exam records for the student improvement MVP."""

from __future__ import annotations

from .models import (
    Chapter,
    Curriculum,
    ExamQuestionResult,
    ExamRecord,
    KnowledgePoint,
    QuestionTemplate,
)


def build_demo_curriculum() -> Curriculum:
    chapters = [
        Chapter(
            chapter_id="ch-fraction",
            title="代数基础与分式",
            summary="建立分式化简与等值变换基础。",
            knowledge_point_ids=["kp-fraction-simplify"],
        ),
        Chapter(
            chapter_id="ch-equation",
            title="一元一次方程",
            summary="掌握移项、去分母和方程求解。",
            knowledge_point_ids=["kp-linear-equation"],
        ),
        Chapter(
            chapter_id="ch-factor",
            title="整式运算与因式分解",
            summary="理解提公因式与平方差分解。",
            knowledge_point_ids=["kp-factorization", "kp-quadratic-expansion"],
        ),
        Chapter(
            chapter_id="ch-function",
            title="一次函数与图像",
            summary="根据表达式和图像理解变量关系。",
            knowledge_point_ids=["kp-linear-function"],
        ),
    ]

    knowledge_points = [
        KnowledgePoint(
            knowledge_point_id="kp-fraction-simplify",
            name="分式化简",
            chapter_id="ch-fraction",
            summary="识别公因式并正确约分。",
            practice_focus=["约分步骤", "分子分母同时约去"],
        ),
        KnowledgePoint(
            knowledge_point_id="kp-linear-equation",
            name="一元一次方程求解",
            chapter_id="ch-equation",
            summary="会移项、合并同类项并检验结果。",
            prerequisites=["kp-fraction-simplify"],
            practice_focus=["去分母", "移项检验"],
        ),
        KnowledgePoint(
            knowledge_point_id="kp-factorization",
            name="提公因式与因式分解",
            chapter_id="ch-factor",
            summary="识别公因式并拆解多项式。",
            practice_focus=["提公因式", "结构识别"],
        ),
        KnowledgePoint(
            knowledge_point_id="kp-quadratic-expansion",
            name="整式展开与化简",
            chapter_id="ch-factor",
            summary="会利用乘法公式展开并合并同类项。",
            prerequisites=["kp-factorization"],
            practice_focus=["平方公式", "符号判断"],
        ),
        KnowledgePoint(
            knowledge_point_id="kp-linear-function",
            name="一次函数理解",
            chapter_id="ch-function",
            summary="根据表达式与图像判断斜率、截距和变化趋势。",
            prerequisites=["kp-linear-equation"],
            practice_focus=["图像判读", "斜率含义", "表达式代入"],
        ),
    ]

    question_bank = [
        QuestionTemplate(
            question_id="ALG-FR-01",
            prompt="化简分式 6x/9x。",
            correct_answer="2/3",
            solution_steps=[
                "观察分子分母的公因式是 3x。",
                "分子分母同时除以 3x。",
                "得到最简结果 2/3。",
            ],
            knowledge_point_ids=["kp-fraction-simplify"],
            tags=["约分", "分式"],
        ),
        QuestionTemplate(
            question_id="ALG-EQ-01",
            prompt="解方程 3x - 5 = 10。",
            correct_answer="x = 5",
            solution_steps=[
                "先两边同时加 5，得到 3x = 15。",
                "再两边同时除以 3，得到 x = 5。",
                "把 x = 5 代回原式完成检验。",
            ],
            knowledge_point_ids=["kp-linear-equation"],
            tags=["移项", "方程"],
        ),
        QuestionTemplate(
            question_id="ALG-FA-01",
            prompt="分解因式 2x^2 + 4x。",
            correct_answer="2x(x + 2)",
            solution_steps=[
                "找出各项公因式 2x。",
                "把 2x 提到括号外。",
                "括号内剩下 x + 2，得到 2x(x + 2)。",
            ],
            knowledge_point_ids=["kp-factorization"],
            tags=["提公因式", "整式"],
        ),
        QuestionTemplate(
            question_id="ALG-FN-01",
            prompt="已知一次函数 y = 2x + 1，求 x = 3 时的 y 值。",
            correct_answer="7",
            solution_steps=[
                "把 x = 3 代入 y = 2x + 1。",
                "先算 2 × 3 = 6。",
                "再算 6 + 1 = 7。",
            ],
            knowledge_point_ids=["kp-linear-function"],
            tags=["代入", "函数"],
        ),
        QuestionTemplate(
            question_id="ALG-FR-02",
            prompt="化简分式 8y/12y。",
            correct_answer="2/3",
            solution_steps=[
                "找出分子分母公因式 4y。",
                "分子分母同除以 4y。",
                "得到最简结果 2/3。",
            ],
            knowledge_point_ids=["kp-fraction-simplify"],
            tags=["约分", "分式"],
        ),
        QuestionTemplate(
            question_id="ALG-EQ-02",
            prompt="解方程 2x + 4 = 12。",
            correct_answer="x = 4",
            solution_steps=[
                "先两边同时减 4，得到 2x = 8。",
                "再两边同时除以 2，得到 x = 4。",
                "代回原式检查结果是否成立。",
            ],
            knowledge_point_ids=["kp-linear-equation"],
            tags=["移项", "方程"],
        ),
        QuestionTemplate(
            question_id="ALG-FN-02",
            prompt="一次函数 y = -x + 5 的斜率是多少？",
            correct_answer="-1",
            solution_steps=[
                "一次函数标准形式是 y = kx + b。",
                "比较 y = -x + 5，可知 k = -1。",
                "因此斜率是 -1。",
            ],
            knowledge_point_ids=["kp-linear-function"],
            tags=["斜率", "函数图像"],
        ),
        QuestionTemplate(
            question_id="ALG-QE-01",
            prompt="展开 (x + 2)^2。",
            correct_answer="x^2 + 4x + 4",
            solution_steps=[
                "应用平方公式 (a + b)^2 = a^2 + 2ab + b^2。",
                "令 a = x，b = 2。",
                "得到 x^2 + 4x + 4。",
            ],
            knowledge_point_ids=["kp-quadratic-expansion"],
            tags=["展开", "平方公式"],
        ),
    ]

    return Curriculum(
        curriculum_id="curriculum-grade8-math-mvp",
        grade="八年级",
        subject="数学",
        chapters=chapters,
        knowledge_points=knowledge_points,
        question_bank=question_bank,
        question_to_knowledge_map={
            item.question_id: list(item.knowledge_point_ids) for item in question_bank
        },
    )


def build_demo_exam_records() -> list[ExamRecord]:
    return [
        ExamRecord(
            exam_id="exam-2026-01",
            student_id="stu-demo-001",
            grade="八年级",
            subject="数学",
            submitted_at="2026-04-01T09:00:00",
            questions=[
                ExamQuestionResult(
                    question_id="ALG-FR-01",
                    prompt="化简分式 6x/9x。",
                    student_answer="6/9",
                    correct_answer="2/3",
                    score=0,
                    full_score=10,
                ),
                ExamQuestionResult(
                    question_id="ALG-EQ-01",
                    prompt="解方程 3x - 5 = 10。",
                    student_answer="x = 15",
                    correct_answer="x = 5",
                    score=0,
                    full_score=10,
                ),
                ExamQuestionResult(
                    question_id="ALG-FA-01",
                    prompt="分解因式 2x^2 + 4x。",
                    student_answer="2x(x + 2)",
                    correct_answer="2x(x + 2)",
                    score=10,
                    full_score=10,
                ),
                ExamQuestionResult(
                    question_id="ALG-FN-01",
                    prompt="已知一次函数 y = 2x + 1，求 x = 3 时的 y 值。",
                    student_answer="5",
                    correct_answer="7",
                    score=0,
                    full_score=10,
                ),
            ],
            total_score=10,
            max_score=40,
        ),
        ExamRecord(
            exam_id="exam-2026-02",
            student_id="stu-demo-001",
            grade="八年级",
            subject="数学",
            submitted_at="2026-04-15T09:00:00",
            questions=[
                ExamQuestionResult(
                    question_id="ALG-FR-02",
                    prompt="化简分式 8y/12y。",
                    student_answer="2/3",
                    correct_answer="2/3",
                    score=10,
                    full_score=10,
                ),
                ExamQuestionResult(
                    question_id="ALG-EQ-02",
                    prompt="解方程 2x + 4 = 12。",
                    student_answer="x = 4",
                    correct_answer="x = 4",
                    score=10,
                    full_score=10,
                ),
                ExamQuestionResult(
                    question_id="ALG-FN-02",
                    prompt="一次函数 y = -x + 5 的斜率是多少？",
                    student_answer="1",
                    correct_answer="-1",
                    score=0,
                    full_score=10,
                ),
                ExamQuestionResult(
                    question_id="ALG-QE-01",
                    prompt="展开 (x + 2)^2。",
                    student_answer="x^2 + 4x + 4",
                    correct_answer="x^2 + 4x + 4",
                    score=10,
                    full_score=10,
                ),
            ],
            total_score=30,
            max_score=40,
        ),
    ]
