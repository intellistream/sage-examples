from sage.apps.student_improvement import StudentImprovementApplicationService
from sage.apps.student_improvement.demo_data import build_demo_curriculum, build_demo_exam_records


def test_initialize_curriculum_success(tmp_path) -> None:
    service = StudentImprovementApplicationService(storage_path=tmp_path / "student-state.json")

    result = service.initialize_curriculum(build_demo_curriculum())

    assert result.curriculum_id == "curriculum-grade8-math-mvp"
    assert result.chapter_count == 4
    assert result.knowledge_point_count == 5
    assert result.question_count == 8


def test_import_exam_generates_wrong_question_diagnosis(tmp_path) -> None:
    service = StudentImprovementApplicationService(storage_path=tmp_path / "student-state.json")
    exams = build_demo_exam_records()
    service.initialize_curriculum(build_demo_curriculum())

    result = service.import_exam(exams[0])

    assert result.wrong_question_count == 3
    assert len(result.wrong_questions) == 3
    assert all(item.standard_solution for item in result.wrong_questions)
    assert result.diagnosis.weak_knowledge_points
    assert "kp-linear-function" in result.diagnosis.mastery_summary


def test_two_exam_imports_update_student_state(tmp_path) -> None:
    service = StudentImprovementApplicationService(storage_path=tmp_path / "student-state.json")
    exams = build_demo_exam_records()
    service.initialize_curriculum(build_demo_curriculum())

    first_result = service.import_exam(exams[0])
    second_result = service.import_exam(exams[1])
    profile = service.get_student_profile(exams[0].student_id)
    imported_exams = service.list_student_exams(exams[0].student_id)

    assert len(imported_exams) == 2
    assert (
        second_result.diagnosis.mastery_summary["kp-linear-equation"]
        > first_result.diagnosis.mastery_summary["kp-linear-equation"]
    )
    assert profile.latest_diagnosis_id == second_result.diagnosis.diagnosis_id
    assert profile.study_plan_summary


def test_wrong_question_bank_changes_dynamically(tmp_path) -> None:
    service = StudentImprovementApplicationService(storage_path=tmp_path / "student-state.json")
    exams = build_demo_exam_records()
    service.initialize_curriculum(build_demo_curriculum())

    service.import_exam(exams[0])
    service.import_exam(exams[1])
    wrong_bank = {item.question_id: item for item in service.get_wrong_question_bank(exams[0].student_id)}

    assert wrong_bank["ALG-EQ-01"].mastery_status == "reviewing"
    assert wrong_bank["ALG-FR-01"].mastery_status == "reviewing"
    assert wrong_bank["ALG-FN-01"].mastery_status == "unmastered"
    assert wrong_bank["ALG-FN-02"].mastery_status == "unmastered"


def test_study_plan_structure_is_stable(tmp_path) -> None:
    service = StudentImprovementApplicationService(storage_path=tmp_path / "student-state.json")
    exams = build_demo_exam_records()
    service.initialize_curriculum(build_demo_curriculum())

    result = service.import_exam(exams[0])

    assert len(result.diagnosis.study_plan) >= 3
    assert all(step.title for step in result.diagnosis.study_plan)
    assert all(step.recommended_actions for step in result.diagnosis.study_plan)
    assert all(isinstance(step.target_knowledge_points, list) for step in result.diagnosis.study_plan)


def test_knowledge_graph_marks_mastery_status(tmp_path) -> None:
    service = StudentImprovementApplicationService(storage_path=tmp_path / "student-state.json")
    exams = build_demo_exam_records()
    service.initialize_curriculum(build_demo_curriculum())
    service.import_exam(exams[0])
    service.import_exam(exams[1])

    graph = service.get_student_knowledge_graph(exams[0].student_id)
    nodes = {node.node_id: node for node in graph.nodes if node.node_type == "knowledge_point"}

    assert graph.student_id == exams[0].student_id
    assert nodes["kp-linear-equation"].mastery_status == "reviewing"
    assert nodes["kp-linear-function"].mastery_status == "unmastered"
    assert nodes["kp-linear-equation"].mastery_score is not None
    assert any(edge.relation == "prerequisite_of" for edge in graph.edges)
